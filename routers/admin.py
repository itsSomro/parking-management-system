from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse
import plotly.graph_objects as go
import pandas as pd

from db.Database import Database
from core.ParkingLot import ParkingLot


router = APIRouter()
db = Database()
parking_lot = ParkingLot(db)

@router.get("/admin/dashboard", response_class=HTMLResponse)
def show_admin_dashboard():
    # ---------------------------------------------------------------------------------------
    # 1. LIVE - STATS TAB
    # ---------------------------------------------------------------------------------------
    stats = parking_lot.get_stats()

    total_spots = parking_lot.get_total_spots_count()
    available_spots = sum(data[0] for data in stats.values())
    occupied_spots = total_spots - available_spots


    # ---------------------------------------------------------------------------------------
    # 2. GRAPHS TAB
    # ---------------------------------------------------------------------------------------
    df = db.get_financial_history()

    if df.empty:
        return (""" <h2 style='color: white; text-align: center; padding-top: 50px;
                font-family: sans-serif; background-color: #121212; height: 100vh; 
                margin: 0;'>No parking data available yet.</h2> """)

    # DATA PREP
    df['Date'] = df['entry_time'].dt.date
    df['Hour'] = df['entry_time'].dt.hour

    # -----------------------------------------------------------------------
    # GRAPH 1: PROFITS/EARNINGS (day/week/month)
    revenue_df = df.dropna(subset=['fee']).groupby('Date')['fee'].sum().reset_index()
    total_revenue = revenue_df['fee'].sum()

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x = revenue_df['Date'], y = revenue_df['fee'],
        mode = 'lines', line = dict(color='#00d09c', width=3),
        hovertemplate = '₹%{y:,.2f} | %{x}<extra></extra>'
    ))
    fig1.update_layout(
        height=220,
        plot_bgcolor = '#121212', paper_bgcolor = '#121212', margin = dict(l=10, r=10, t=10, b=50),
        hovermode = 'x unified',
        hoverlabel=dict(
            bgcolor="#2a2a2a",
            font=dict(color="white")
        ),
        xaxis = dict(
            showgrid=False, showline=False,
            showspikes=False,
            tickfont=dict(color="#aaaaaa"),
            rangeselector = dict(
                buttons = list([
                    dict(count=7, label="1W", step="day", stepmode="backward"),
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(step="all", label="ALL")
                ]),
                x=0.5, y=-0.15, xanchor='center', yanchor='top',
                bgcolor='#121212', activecolor='#2a2a2a', font=dict(color="white")
            )
        ),
        yaxis = dict(showgrid=False, visible=False)
    )

    # -----------------------------------------------------------------------
    # GRAPH 2: VEHICLE ENTRIES (day/week/month)
    entries_df = df.groupby('Date').size().reset_index(name='Total Entries')
    total_entries = entries_df['Total Entries'].sum()

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x = entries_df['Date'], y = entries_df['Total Entries'],
        marker = dict(color='#3498db'),
        hovertemplate = '%{y} Vehicles | %{x}<extra></extra>'
    ))
    fig2.update_layout(
        height = 220,
        plot_bgcolor = '#121212', paper_bgcolor = '#121212', margin = dict(l=10, r=10, t=10, b=50),
        hovermode = 'x unified',
        hoverlabel=dict(
            bgcolor="#2a2a2a",
            font=dict(color="white")
        ),
        xaxis = dict(
            showgrid=False, showline=False, showspikes=False,
            tickfont=dict(color="#aaaaaa"),
            rangeselector = dict(
                buttons = list([
                    dict(count=7, label="1W", step="day", stepmode="backward"),
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(step="all", label="ALL")
                ]),
                x=0.5, y=-0.15, xanchor='center', yanchor='top',
                bgcolor='#121212', activecolor='#2a2a2a', font=dict(color="white")
            )
        ),
        yaxis = dict(showgrid=False, visible=False)
    )

    # -----------------------------------------------------------------------
    # GRAPH 3: PEAK HOURS (dropdown for last 7 days)
    fig3 = go.Figure()
    last_7_days = sorted(df['Date'].unique())[-7:]
    dropdown_buttons = []

    for i, day in enumerate(last_7_days):
        day_data = df[df['Date'] == day]
        hourly_counts = day_data.groupby('Hour').size().reset_index(name='Entries')

        fig3.add_trace(go.Bar(
            x = hourly_counts['Hour'], y = hourly_counts['Entries'],
            name = str(day), visible = (i == len(last_7_days) - 1),
            marker = dict(color='#f39c12'),
            hovertemplate = '%{y} Vehicles at %{x}:00<extra></extra>'
        ))

        visibility = [False] * len(last_7_days)
        visibility[i] = True
        dropdown_buttons.append(dict(
            label=day.strftime('%b %d, %Y'), method="update",
            args=[{"visible": visibility}, {"title": f"Peak Hours for {day.strftime('%b %d')}"}]
        ))

    fig3.update_layout(
        height = 400,
        plot_bgcolor='#121212', paper_bgcolor='#121212', margin=dict(l=20, r=20, t=60, b=20),
        title=dict(text=f"Peak Hours for {last_7_days[-1].strftime('%b %d') if last_7_days else 'Recent'}",
                   font=dict(color="white")),
        xaxis=dict(showgrid=False, title="Hour of the Day (0-23)", color="white",
                   range=[-0.5, 23.5], tickmode='linear', dtick=1),
        yaxis=dict(showgrid=False, visible=False),
        updatemenus=[dict(
            active=len(last_7_days) - 1, buttons=dropdown_buttons,
            x=1.0, y=1.15, bgcolor="#2a2a2a", font=dict(color="white")
        )]
    )

    # ---------------------------------------------------------------------------------------
    # RENDER TO HTML
    # ---------------------------------------------------------------------------------------
    html_content = f"""
            <html>
                <head>
                    <title>Admin Hub</title>
                    <style>
                        body {{
                            background-color: #121212; 
                            color: white; 
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                            padding: 30px;
                            max-width: 1100px;
                            margin: 0 auto;
                        }}
                        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&display=swap');
                        
                        h1.main-title {{ 
                        text-align: center; 
                        margin-bottom: 35px; 
                        font-family: 'Cinzel', serif, Times New Roman;
                        font-weight: 800; 
                        font-size: 3.8rem;
                        color: #ffffff;
                        letter-spacing: 4px;
                        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                    }}
                        .subtitle {{
                        display: block;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        font-weight: 400;
                        color: #888888;
                        font-size: 1rem;
                        margin-top: 10px;
                        letter-spacing: 6px;
                        text-transform: uppercase;
                    }}

                        /* LIVE STATS UI */
                        .stats-container {{ display: flex; justify-content: space-between; background-color: #1e1e1e; padding: 20px 30px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #333; }}
                        .stat-box h3 {{ margin: 0; color: #e0e0e0; font-size: 1.15rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
                        .stat-box h1 {{ margin: 5px 0 5px 0; font-size: 2.5rem; color: #ffffff; }}
                        .stat-box p {{ margin: 5px 0 0 0; font-size: 1rem; color: #cccccc; font-weight: 500; word-spacing: 2px; }}

                        /* MAP DROPDOWN */
                        details {{ background-color: #1e1e1e; border: 1px solid #333; border-radius: 12px; margin-bottom: 30px; overflow: hidden; }}
                        summary {{ padding: 20px; font-size: 1.2rem; font-weight: bold; cursor: pointer; list-style: none; text-align: center; background-color: #2a2a2a; transition: background 0.2s; }}
                        summary:hover {{ background-color: #333; }}
                        .map-placeholder {{ padding: 40px; text-align: center; color: #777; font-style: italic; min-height: 200px; }}

                        /* ROUTING BUTTONS */
                        .button-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 50px; }}
                        .nav-btn {{ display: block; text-align: center; background-color: #3498db; color: white; text-decoration: none; padding: 20px 15px; border-radius: 12px; font-size: 1.1rem; font-weight: bold; transition: transform 0.2s, background 0.2s; }}
                        .nav-btn:hover {{ transform: translateY(-5px); background-color: #2980b9; }}
                        
                        .nav-btn.configure {{ background-color: #27ae60; }}
                        .nav-btn.configure:hover {{ background-color: #219653; }}
                        
                        .nav-btn.users {{ background-color: #2980b9; }}
                        .nav-btn.users:hover {{ background-color: #1f618d; }}
                    
                        .nav-btn.operator {{ background-color: #f39c12; }}
                        .nav-btn.operator:hover {{ background-color: #d68910; }}

                        /* GRAPHS UI */
                        .dashboard-grid {{ display: flex; justify-content: space-between; margin-bottom: 40px; gap: 20px; }}
                        .card {{ width: 48%; background-color: #1e1e1e; border: 1px solid #333; border-radius: 12px; padding: 20px; box-sizing: border-box; }}
                        .kpi-title {{ font-size: 1rem; color: #aaaaaa; margin-bottom: 5px; }}
                        .kpi-value-green {{ font-size: 2.5rem; font-weight: bold; color: #00d09c; margin: 0 0 15px 0; }}
                        .kpi-value-blue {{ font-size: 2.5rem; font-weight: bold; color: #3498db; margin: 0 0 15px 0; }}
                        .full-width-card {{ width: 100%; background-color: #1e1e1e; border: 1px solid #333; border-radius: 12px; padding: 20px; box-sizing: border-box; margin-bottom: 40px; }}

                        /* LOGOUT BUTTON */
                        .logout-btn {{ display: block; width: 200px; margin: 0 auto; text-align: center; background-color: transparent; color: #e74c3c; text-decoration: none; padding: 15px; border: 2px solid #e74c3c; border-radius: 8px; font-weight: bold; transition: all 0.2s; }}
                        .logout-btn:hover {{ background-color: #e74c3c; color: white; }}
                    </style>
                </head>
                <body>
                    <h1 class="main-title">ParkSmart<span class="subtitle">Admin Dashboard</span></h1>

                    <!-- 1. LIVE TRACKER -->
                    <div class="stats-container">
                        <div class="stat-box">
                            <h3 style="color: #00d09c;">Available Spots</h3>
                            <h1>{available_spots}</h1>
                            <p>Cars: {stats.get('C', (0, 0))[0]} | Bikes: {stats.get('T', (0, 0))[0]} | Heavy: {stats.get('S', (0, 0))[0]}</p>
                        </div>
                        <div class="stat-box occupied" style="text-align: center;">
                            <h3 style="color: #e74c3c;">Occupied</h3>
                            <h1>{occupied_spots}</h1>
                            <p>Cars: {stats.get('C', (0, 0))[1] - stats.get('C', (0, 0))[0]} | Bikes: {stats.get('T', (0, 0))[1] - stats.get('T', (0, 0))[0]} | Heavy: {stats.get('S', (0, 0))[1] - stats.get('S', (0, 0))[0]}</p>
                        </div>
                        <div class="stat-box" style="text-align: right;">
                            <h3 style="color: #3498db;">Total Capacity</h3>
                            <h1 style="color: white;">{total_spots}</h1>
                            <p>Cars: {stats.get('C', (0, 0))[1]} | Bikes: {stats.get('T', (0, 0))[1]} | Heavy: {stats.get('S', (0, 0))[1]}</p>
                        </div>
                    </div>

                    <!-- 2. MAP DROPDOWN -->
                    <details>
                        <summary>🗺️ View Live Parking Map</summary>
                        <div class="map-placeholder">
                            (Map Grid renders here later)
                        </div>
                    </details>

                    <!-- 3. NAVIGATION HUB BUTTONS -->
                    <div class="button-grid">
                        <a href="/admin/configure" class="nav-btn configure">⚙️ Configure Lot</a>
                        <a href="/admin/users" class="nav-btn users">👤 Manage Users</a>
                        <a href="/operator" class="nav-btn operator">🚗 Operator Mode</a>
                    </div>

                    <!-- 4. ANALYTICS GRAPHS -->
                    <h2 style="color: #aaaaaa; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px;">Financial Analytics</h2>
                    <div class="dashboard-grid">
                        <div class="card">
                            <div class="kpi-title">Total Revenue Collected</div>
                            <div class="kpi-value-green">₹{total_revenue:,.2f}</div>
                            <div>{fig1.to_html(full_html=False, config={'displayModeBar': False})}</div>
                        </div>
                        <div class="card">
                            <div class="kpi-title">Total Vehicle Entries</div>
                            <div class="kpi-value-blue">{total_entries:,}</div>
                            <div>{fig2.to_html(full_html=False, config={'displayModeBar': False})}</div>
                        </div>
                    </div>

                    <div class="full-width-card">
                        <div>{fig3.to_html(full_html=False, config={'displayModeBar': False})}</div>
                    </div>

                    <!-- 5. LOGOUT -->
                    <a href="/logout" class="logout-btn">Log Out</a>
                </body>
            </html>
            """
    return HTMLResponse(content=html_content)







