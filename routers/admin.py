from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
import plotly.graph_objects as go
import pandas as pd
from pydantic import BaseModel
from typing import Dict
import json

from db.Database import Database
from core.ParkingLot import ParkingLot


class AddUserSchema(BaseModel):
    username: str
    password: str
    role: str

class SetupLotSchema(BaseModel):
    floor_configs: Dict[int, Dict[str, int]]

class EditRatesSchema(BaseModel):
    car_rate: float
    bike_rate: float
    heavy_rate: float

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
                    
                        .nav-btn.dashboard {{ background-color: #f39c12; }}
                        .nav-btn.dashboard:hover {{ background-color: #d68910; }}

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
                            <p>Car: {stats.get('C', (0, 0))[0]} | Scooter: {stats.get('S', (0, 0))[0]} | Heavy: {stats.get('T', (0, 0))[0]}</p>
                        </div>
                        <div class="stat-box occupied" style="text-align: center;">
                            <h3 style="color: #e74c3c;">Occupied</h3>
                            <h1>{occupied_spots}</h1>
                            <p>Car: {stats.get('C', (0, 0))[1] - stats.get('C', (0, 0))[0]} | Scooter: {stats.get('S', (0, 0))[1] - stats.get('S', (0, 0))[0]} | Heavy: {stats.get('T', (0, 0))[1] - stats.get('T', (0, 0))[0]}</p>
                        </div>
                        <div class="stat-box" style="text-align: right;">
                            <h3 style="color: #3498db;">Total Capacity</h3>
                            <h1 style="color: white;">{total_spots}</h1>
                            <p>Car: {stats.get('C', (0, 0))[1]} | Scooter: {stats.get('S', (0, 0))[1]} | Heavy: {stats.get('T', (0, 0))[1]}</p>
                        </div>
                    </div>

                    <!-- 2. MAP DROPDOWN -->
                    <details style="background-color: #1e1e1e; border: 1px solid #333; border-radius: 12px; margin-bottom: 30px; overflow: hidden;">
                        <summary style="padding: 20px; font-size: 1.2rem; font-weight: bold; cursor: pointer; list-style: none; text-align: center; background-color: #2a2a2a; transition: background 0.2s;">🗺️ View Live Parking Map</summary>
                        
                        <style>
                            /* Live Map Grid Styles */
                            .map-container {{ padding: 20px; text-align: left; background-color: #121212; }}
                            .spot-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 15px; }}
                            
                            .spot-card {{
                                border-radius: 8px; padding: 15px 10px; text-align: center; 
                                font-family: monospace; font-weight: bold; font-size: 14px;
                                display: flex; flex-direction: column; gap: 5px; transition: all 0.2s;
                            }}
                    
                            /* Type Colors */
                            .spot-type-S {{ color: #3b82f6; }}
                            .spot-type-C {{color: #22c55e; }}
                            .spot-type-T {{ color: #f97316; }}
                            
                            /* Status Styles */
                            .spot-free {{ border: 1px solid currentcolor; opacity: 0.4; background-color: transparent; }}
                            .spot-occupied {{ border: 2px solid currentcolor; background-color: #1a1a1a; color: #fff; box-shadow: 0 4px 10px rgba(0,0,0,0.4); opacity: 1; }}
                            .plate-badge {{ background-color: #fff; color: #000; padding: 3px 6px; border-radius: 4px; font-size: 13px; margin-top: 5px; display: inline-block; box-shadow: inset 0 0 5px rgba(0,0,0,0.2); }}
                        </style>
                    
                        <div id="liveMapContainer" class="map-container">
                            <!-- Floor Controller -->
                            <div id="mapControls" style="display: none; justify-content: space-between; align-items: center; margin-bottom: 25px; padding: 0 10px;">
                                <label for="floorSelect" style="font-weight: bold; color: #aaa; text-transform: uppercase; letter-spacing: 1px;">Display Level:</label>
                                <select id="floorSelect" style="padding: 10px 20px; border-radius: 8px; background: #1a1a1a; color: white; border: 1px solid #333; font-size: 16px; outline: none; cursor: pointer; font-weight: bold;">
                                    <!-- Options populated by JS -->
                                </select>
                            </div>
                            
                            <div id="floorViewsWrapper">
                                <p id="loadingText" style="text-align: center; color: #888;">Loading map data...</p>
                            </div>
                        </div>
                    </details>

                    <!-- 3. NAVIGATION HUB BUTTONS -->
                    <div class="button-grid">
                        <a href="/admin/configure" class="nav-btn configure">⚙️ Configure Lot</a>
                        <a href="/admin/users" class="nav-btn users">👤 Manage Users</a>
                        <a href="/operator/dashboard" class="nav-btn dashboard">🚗 Operator Mode</a>
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
                </div>
                
                    <!-- LIVE MAP JAVASCRIPT -->
                    <script>
                        async function loadLiveMap() {{
                            try {{
                                const response = await fetch('/operator/api/live-map');
                                const data = await response.json();

                                if (data.status === 'success') {{
                                    const wrapper = document.getElementById('floorViewsWrapper');
                                    const select = document.getElementById('floorSelect');
                                    const controls = document.getElementById('mapControls');

                                    wrapper.innerHTML = '';
                                    select.innerHTML = '';

                                    let firstFloor = null;

                                    for (const [floorNum, spots] of Object.entries(data.floors)) {{
                                        if (firstFloor === null) firstFloor = floorNum;

                                        // Create Dropdown Option
                                        const opt = document.createElement('option');
                                        opt.value = floorNum;
                                        opt.textContent = 'Level ' + floorNum;
                                        select.appendChild(opt);

                                        // Create Floor Grid Wrapper
                                        const floorDiv = document.createElement('div');
                                        floorDiv.className = 'floor-section';
                                        floorDiv.id = 'floor-view-' + floorNum;
                                        floorDiv.style.display = 'none'; // Hidden by default

                                        const gridDiv = document.createElement('div');
                                        gridDiv.className = 'spot-grid';

                                        spots.forEach(spot => {{
                                            const spotDiv = document.createElement('div');
                                            const typeClass = 'spot-type-' + spot.type;
                                            const statusClass = spot.is_free ? 'spot-free' : 'spot-occupied';
                                            spotDiv.className = 'spot-card ' + typeClass + ' ' + statusClass;

                                            if (spot.is_free) {{
                                                spotDiv.innerHTML = '<span>' + spot.spot_id + '</span><span style="font-size: 10px; font-weight: normal;">AVAILABLE</span>';
                                            }} else {{
                                                spotDiv.innerHTML = '<span style="color: currentcolor">' + spot.spot_id + '</span><span class="plate-badge">' + spot.plate + '</span>';
                                            }}
                                            gridDiv.appendChild(spotDiv);
                                        }});

                                        floorDiv.appendChild(gridDiv);
                                        wrapper.appendChild(floorDiv);
                                    }}

                                    controls.style.display = 'flex';
                                    if (firstFloor !== null) {{
                                        document.getElementById('floor-view-' + firstFloor).style.display = 'block';
                                    }}

                                    select.onchange = function() {{
                                        document.querySelectorAll('.floor-section').forEach(el => el.style.display = 'none');
                                        document.getElementById('floor-view-' + this.value).style.display = 'block';
                                    }};
                                }}
                            }} catch (e) {{
                                document.getElementById('loadingText').innerHTML = '<span style="color: #ef4444;">Failed to load map.</span>';
                            }}
                        }}

                        document.querySelector('details').addEventListener('toggle', function(e) {{
                            if (e.target.open) {{
                                loadLiveMap();
                            }}
                        }});
                    </script>
                </body>
            </html>
            """
    return HTMLResponse(content=html_content)


@router.get("/admin/configure", response_class=HTMLResponse)
async def configure_lot():
    stats = parking_lot.get_stats()
    rates = db.get_current_rates()

    bike_capacity = stats.get('S', (0, 0))[1]
    car_capacity = stats.get('C', (0, 0))[1]
    heavy_capacity = stats.get('T', (0, 0))[1]

    bike_rate = rates.get('S', 0.0)
    car_rate = rates.get('C', 0.0)
    heavy_rate = rates.get('T', 0.0)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Configure Lot - ParkSmart</title>
        <style>
            /* Import the Roman font */
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&display=swap');

            body {{
                background-color: #121212;
                color: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                margin: 0;
                padding: 50px;
            }}

            /* TITLE STYLES */
            h1.main-title {{ 
                text-align: center; 
                margin-bottom: 50px; 
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

            /* DATA VIEWS (Capacity & Rates) */
            .info-container {{ 
                display: flex; 
                justify-content: center; 
                gap: 40px; 
                margin-bottom: 60px; 
            }}

            .info-box {{ 
                background-color: #1e1e1e; 
                padding: 30px 40px; 
                border-radius: 12px; 
                border: 1px solid #333; 
                min-width: 320px;
            }}

            .info-box h3 {{ 
                margin: 0 0 20px 0; 
                font-size: 1.2rem; 
                color: #e0e0e0; 
                text-align: center;
                text-transform: uppercase; 
                letter-spacing: 1px; 
                border-bottom: 1px solid #333;
                padding-bottom: 15px;
            }}

            .data-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                font-size: 1.15rem;
            }}
            .data-row:last-child {{ margin-bottom: 0; }}

            .data-label {{ color: #aaaaaa; font-weight: 500; }}
            .data-capacity {{ color: #00d09c; font-weight: bold; font-size: 1.4rem; }}
            .data-rate {{ color: #3498db; font-weight: bold; font-size: 1.4rem; }}

            /* ACTION BUTTONS */
            .button-grid {{ 
                display: grid; 
                grid-template-columns: repeat(3, 1fr); 
                gap: 20px; 
                max-width: 1000px;
                margin: 0 auto;
            }}

            .nav-btn {{ 
                display: block; 
                text-align: center; 
                color: white; 
                text-decoration: none; 
                padding: 25px 15px; 
                border-radius: 12px; 
                font-size: 1.2rem; 
                font-weight: bold; 
                transition: transform 0.2s, background 0.2s; 
                border: none;
                cursor: pointer;
            }}
            .nav-btn:hover {{ transform: translateY(-5px); }}

            .nav-btn.setup {{ background-color: #27ae60; }}
            .nav-btn.setup:hover {{ background-color: #219653; }}

            .nav-btn.edit-lot {{ background-color: #2980b9; }}
            .nav-btn.edit-lot:hover {{ background-color: #1f618d; }}

            .nav-btn.edit-rates {{ background-color: #f39c12; }}
            .nav-btn.edit-rates:hover {{ background-color: #d68910; }}

            /* BACK NAVIGATION */
            .back-nav {{
                text-align: center;
                margin-top: 60px;
            }}
            .back-nav a {{
                color: #888888;
                text-decoration: none;
                font-size: 1.1rem;
                transition: color 0.2s;
            }}
            .back-nav a:hover {{ color: #ffffff; }}
        </style>
    </head>
    <body>

        <h1 class="main-title">ParkSmart<span class="subtitle">Configuration Center</span></h1>

        <!-- 1. DATA VIEWS -->
        <div class="info-container">

            <!-- Capacity Card -->
            <div class="info-box">
                <h3>Total Lot Capacity</h3>
                <div class="data-row">
                    <span class="data-label">🏍️ Two-Wheeler</span>
                    <span class="data-capacity">{bike_capacity}</span>
                </div>
                <div class="data-row">
                    <span class="data-label">🚗 Cars</span>
                    <span class="data-capacity">{car_capacity}</span>
                </div>
                <div class="data-row">
                    <span class="data-label">🛻 Heavy Vehicles</span>
                    <span class="data-capacity">{heavy_capacity}</span>
                </div>
            </div>

            <!-- Billing Rates Card -->
            <div class="info-box">
                <h3>Current Hourly Rates</h3>
                <div class="data-row">
                    <span class="data-label">🏍️ Two-Wheeler</span>
                    <span class="data-rate">₹{bike_rate:.2f}</span>
                </div>
                <div class="data-row">
                    <span class="data-label">🚗 Cars</span>
                    <span class="data-rate">₹{car_rate:.2f}</span>
                </div>
                <div class="data-row">
                    <span class="data-label">🛻 Heavy Vehicles</span>
                    <span class="data-rate">₹{heavy_rate:.2f}</span>
                </div>
            </div>

        </div>

        <!-- 2. CONFIGURATION ACTIONS -->
        <div class="button-grid">
            <a href="/admin/configure/setup" class="nav-btn setup">➕ Setup New Lot</a>
            <a href="/admin/configure/edit-lot" class="nav-btn edit-lot">🏗️ Edit Existing Lot</a>
            <a href="/admin/configure/edit-rates" class="nav-btn edit-rates">💰 Edit Billing Rates</a>
        </div>

        <!-- 3. BACK BUTTON -->
        <div class="back-nav">
            <a href="/admin/dashboard">← Back to Admin Dashboard</a>
        </div>

    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@router.get("/admin/configure/setup", response_class=HTMLResponse)
async def setup_new_lot_ui():
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Setup New Lot - ParkSmart</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&display=swap');
            body {{ background-color: #121212; color: #ffffff; font-family: -apple-system, sans-serif; padding: 40px; margin: 0; }}
            h1.main-title {{ text-align: center; font-family: 'Cinzel', serif; font-weight: 800; font-size: 3.2rem; margin-bottom: 10px; color: #ffffff; letter-spacing: 3px; }}
            .subtitle {{ display: block; font-family: sans-serif; font-size: 1rem; color: #888; letter-spacing: 4px; text-transform: uppercase; text-align: center; margin-bottom: 50px; }}

            .form-container {{ background-color: #1e1e1e; max-width: 500px; margin: 0 auto; padding: 30px; border-radius: 12px; border: 1px solid #333; min-height: 300px; }}
            .form-group {{ margin-bottom: 25px; }}
            label {{ display: block; color: #aaaaaa; margin-bottom: 10px; font-weight: bold; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1px; }}
            input[type="number"] {{ width: 100%; padding: 15px; background-color: #2a2a2a; border: 1px solid #444; color: white; border-radius: 6px; font-size: 1.2rem; box-sizing: border-box; text-align: center; }}

            h3.floor-title {{ color: #00d09c; text-align: center; font-size: 1.5rem; margin-top: 0; border-bottom: 1px solid #333; padding-bottom: 15px; margin-bottom: 25px; }}

            .btn-group {{ display: flex; justify-content: space-between; gap: 15px; margin-top: 30px; }}
            .btn {{ flex: 1; padding: 15px; font-size: 1.1rem; font-weight: bold; border-radius: 8px; border: none; cursor: pointer; transition: 0.2s; color: white; }}
            .btn:disabled {{ background-color: #444; color: #777; cursor: not-allowed; }}

            .btn-start {{ background-color: #3498db; width: 100%; }}
            .btn-start:hover {{ background-color: #2980b9; }}

            .btn-nav {{ background-color: #555; }}
            .btn-nav:hover:not(:disabled) {{ background-color: #777; }}

            .btn-next {{ background-color: #3498db; }}
            .btn-next:hover:not(:disabled) {{ background-color: #2980b9; }}

            .btn-confirm {{ background-color: #27ae60; display: none; }}
            .btn-confirm:hover {{ background-color: #219653; }}

            .back-nav {{ text-align: center; margin-top: 40px; }}
            .back-nav a {{ color: #888; text-decoration: none; font-size: 1.1rem; }}
            .back-nav a:hover {{ color: white; }}
        </style>
    </head>
    <body>

        <h1 class="main-title">ParkSmart</h1>
        <span class="subtitle">Lot Initialization Wizard</span>

        <div class="form-container">
            <!-- Step 1: Initial Floor Count -->
            <div id="step-initial">
                <div class="form-group">
                    <label style="text-align: center;">How many floors does the lot have?</label>
                    <input type="number" id="totalFloors" min="1" max="50" placeholder="Enter number of floors">
                </div>
                <button class="btn btn-start" onclick="startWizard()">Start Configuration</button>
            </div>

            <!-- Step 2: Per-Floor Configuration Wizard -->
            <div id="step-wizard" style="display: none;">
                <h3 class="floor-title" id="floorTitle">Input details for Floor 0</h3>

                <div class="form-group">
                    <label>🏍️ Total Two-Wheelers (S) Spots</label>
                    <input type="number" id="input-S" min="0" value="0">
                </div>
                <div class="form-group">
                    <label>🚗 Total Cars (C) Spots</label>
                    <input type="number" id="input-C" min="0" value="0">
                </div>
                <div class="form-group">
                    <label>🛻 Total Heavy Vehicles (T) Spots</label>
                    <input type="number" id="input-T" min="0" value="0">
                </div>

                <div class="btn-group">
                    <button class="btn btn-nav" id="btn-prev" onclick="goPrev()">Previous</button>
                    <button class="btn btn-next" id="btn-next" onclick="goNext()">Next</button>
                    <button class="btn btn-confirm" id="btn-confirm" onclick="submitConfiguration()">Confirm & Save</button>
                </div>
            </div>
        </div>

        <div class="back-nav">
            <a href="/admin/configure">← Back to Configuration Center</a>
        </div>

        <script>
            let totalFloors = 0;
            let currentFloor = 0;
            let lotData = {{}};

            function startWizard() {{
                const inputVal = parseInt(document.getElementById('totalFloors').value);
                if (!inputVal || inputVal < 1) {{ alert("Please enter a valid number of floors."); return; }}

                totalFloors = inputVal;

                for(let i = 0; i < totalFloors; i++) {{
                    lotData[i] = {{ 'C': 0, 'S': 0, 'T': 0 }};
                }}

                document.getElementById('step-initial').style.display = 'none';
                document.getElementById('step-wizard').style.display = 'block';

                renderFloor();
            }}

            function saveCurrentInputs() {{
                lotData[currentFloor]['C'] = parseInt(document.getElementById('input-C').value) || 0;
                lotData[currentFloor]['S'] = parseInt(document.getElementById('input-S').value) || 0;
                lotData[currentFloor]['T'] = parseInt(document.getElementById('input-T').value) || 0;
            }}

            function renderFloor() {{
                document.getElementById('floorTitle').innerText = `Input details for Floor ${{currentFloor}}`;

                document.getElementById('input-C').value = lotData[currentFloor]['C'];
                document.getElementById('input-S').value = lotData[currentFloor]['S'];
                document.getElementById('input-T').value = lotData[currentFloor]['T'];

                document.getElementById('btn-prev').disabled = (currentFloor === 0);

                if (currentFloor === totalFloors - 1) {{
                    document.getElementById('btn-next').style.display = 'none';
                    document.getElementById('btn-confirm').style.display = 'block';
                }} else {{
                    document.getElementById('btn-next').style.display = 'block';
                    document.getElementById('btn-confirm').style.display = 'none';
                }}
            }}

            function goNext() {{
                saveCurrentInputs();
                if (currentFloor < totalFloors - 1) {{
                    currentFloor++;
                    renderFloor();
                }}
            }}

            function goPrev() {{
                saveCurrentInputs();
                if (currentFloor > 0) {{
                    currentFloor--;
                    renderFloor();
                }}
            }}

            async function submitConfiguration() {{
                saveCurrentInputs(); // Make sure the last floor is saved before submitting

                const response = await fetch('/admin/configure/setup', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ floor_configs: lotData }})
                }});

                if (response.ok) {{
                    alert("Lot successfully configured!");
                    window.location.href = '/admin/configure';
                }} else {{
                    alert("Failed to configure lot. Check backend console.");
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.post("/admin/configure/setup")
async def process_setup_lot(data: SetupLotSchema):
    try:
        parking_lot.configure_lot(data.floor_configs)
        return {"status": "success", "message": "Lot configured successfully"}
    except Exception as e:
        print(f"Database error during setup: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/admin/configure/edit-lot", response_class=HTMLResponse)
async def edit_existing_lot_ui():
    # ---------------------------------------------------------------------------
    # 1. Fetch current layout from your database
    current_layout = parking_lot.get_floor_layout()

    # Convert to JSON string to inject into Javascript
    layout_json = json.dumps(current_layout)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Lot - ParkSmart</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&display=swap');
            body {{ background-color: #121212; color: #ffffff; font-family: -apple-system, sans-serif; padding: 40px; margin: 0; }}
            h1.main-title {{ text-align: center; font-family: 'Cinzel', serif; font-weight: 800; font-size: 3.2rem; margin-bottom: 10px; color: #ffffff; letter-spacing: 3px; }}
            .subtitle {{ display: block; font-family: sans-serif; font-size: 1rem; color: #888; letter-spacing: 4px; text-transform: uppercase; text-align: center; margin-bottom: 50px; }}

            .layout-container {{ max-width: 700px; margin: 0 auto; }}

            /* Expandable Floor Boxes */
            .floor-box {{ background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; margin-bottom: 15px; overflow: hidden; transition: 0.3s; }}

            .floor-header {{ background-color: #252525; padding: 20px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: background-color 0.2s; }}
            .floor-header:hover {{ background-color: #2a2a2a; }}
            .floor-title {{ font-size: 1.3rem; font-weight: bold; color: #00d09c; margin: 0; }}
            .floor-summary {{ color: #aaaaaa; font-size: 1.1rem; }}

            /* Hidden Input Panel */
            .floor-body {{ padding: 25px 20px; display: none; background-color: #1e1e1e; border-top: 1px solid #333; }}
            .input-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}

            .form-group label {{ display: block; color: #aaaaaa; margin-bottom: 10px; font-weight: bold; font-size: 1rem; text-align: center; }}
            .form-group input {{ width: 100%; padding: 12px; background-color: #2a2a2a; border: 1px solid #444; color: white; border-radius: 6px; font-size: 1.2rem; text-align: center; box-sizing: border-box; }}

            /* Global Action Buttons */
            .global-actions {{ display: flex; gap: 20px; justify-content: center; margin-top: 40px; max-width: 700px; margin-left: auto; margin-right: auto; }}
            .btn {{ flex: 1; padding: 18px; font-size: 1.2rem; font-weight: bold; border-radius: 8px; border: none; cursor: pointer; transition: 0.2s; color: white; text-align: center; text-decoration: none; }}

            .btn-save {{ background-color: #27ae60; }}
            .btn-save:hover {{ background-color: #219653; transform: translateY(-3px); }}

            .btn-cancel {{ background-color: #e74c3c; }}
            .btn-cancel:hover {{ background-color: #c0392b; transform: translateY(-3px); }}
        </style>
    </head>
    <body>

        <h1 class="main-title">ParkSmart</h1>
        <span class="subtitle">Edit Current Layout</span>

        <div class="layout-container" id="floors-container">
            <!-- JavaScript will populate the floor boxes here -->
        </div>

        <div class="global-actions">
            <a href="/admin/configure" class="btn btn-cancel">Cancel & Revert</a>
            <button class="btn btn-save" onclick="saveEditedLayout()">💾 Save All Changes</button>
        </div>

        <script>
            const lotData = {layout_json};
            const container = document.getElementById('floors-container');

            // 1. Render the Expandable Boxes
            function renderLayout() {{
                container.innerHTML = '';

                for (const [floor, spots] of Object.entries(lotData)) {{
                    const html = `
                        <div class="floor-box" id="floor-box-${{floor}}">
                            <div class="floor-header" onclick="toggleFloor(${{floor}})">
                                <h3 class="floor-title">Floor ${{floor}}</h3>
                                <div class="floor-summary" id="summary-${{floor}}">
                                    🏍️ ${{spots['S']}} | 🚗 ${{spots['C']}} | 🛻 ${{spots['T']}}
                                </div>
                            </div>
                            <div class="floor-body" id="body-${{floor}}">
                                <div class="input-grid">
                                    <div class="form-group">
                                        <label>Cars (C)</label>
                                        <input type="number" class="edit-input" data-floor="${{floor}}" data-vtype="C" min="0" value="${{spots['C']}}" onchange="updateSummary(${{floor}})">
                                    </div>
                                    <div class="form-group">
                                        <label>Bikes (S)</label>
                                        <input type="number" class="edit-input" data-floor="${{floor}}" data-vtype="S" min="0" value="${{spots['S']}}" onchange="updateSummary(${{floor}})">
                                    </div>
                                    <div class="form-group">
                                        <label>Heavy (T)</label>
                                        <input type="number" class="edit-input" data-floor="${{floor}}" data-vtype="T" min="0" value="${{spots['T']}}" onchange="updateSummary(${{floor}})">
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    container.innerHTML += html;
                }}
            }}

            // 2. Accordion Toggle Mechanic
            function toggleFloor(floorId) {{
                const body = document.getElementById(`body-${{floorId}}`);
                if (body.style.display === 'block') {{
                    body.style.display = 'none';
                }} else {{
                    document.querySelectorAll('.floor-body').forEach(el => el.style.display = 'none');
                    body.style.display = 'block';
                }}
            }}

            // 3. Live Update the Summary text when typing
            function updateSummary(floorId) {{
                const inputs = document.querySelectorAll(`.edit-input[data-floor="${{floorId}}"]`);
                let c = 0, s = 0, t = 0;

                inputs.forEach(input => {{
                    if (input.dataset.vtype === 'C') c = input.value || 0;
                    if (input.dataset.vtype === 'S') s = input.value || 0;
                    if (input.dataset.vtype === 'T') t = input.value || 0;
                }});

                document.getElementById(`summary-${{floorId}}`).innerText = ` 🏍️ ${{s}} | 🚗 ${{c}} | 🛻 ${{t}}`;
            }}

            // 4. Submit to Backend
            async function saveEditedLayout() {{
                const newLayout = {{}};

                document.querySelectorAll('.edit-input').forEach(input => {{
                    const floor = parseInt(input.dataset.floor);
                    const vType = input.dataset.vtype;
                    const val = parseInt(input.value) || 0;

                    if (!newLayout[floor]) newLayout[floor] = {{}};
                    newLayout[floor][vType] = val;
                }});

                const response = await fetch('/admin/configure/edit-lot', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ floor_configs: newLayout }})
                }});

                if (response.ok) {{
                    alert("Lot layout updated successfully!");
                    window.location.href = '/admin/configure';
                }} else {{
                    alert("Failed to update layout. Check backend console.");
                }}
            }}

            // Run on load
            renderLayout();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.post("/admin/configure/edit-lot")
async def process_edit_lot(data: SetupLotSchema):
    try:
        parking_lot.configure_lot(data.floor_configs)
        return {"status": "success", "message": "Lot updated successfully"}
    except Exception as e:
        print(f"ParkingLot error during edit: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/admin/configure/edit-rates", response_class=HTMLResponse)
async def edit_rates_ui():
    rates = db.get_current_rates()

    bike_rate = rates.get('S', 0.0)
    car_rate = rates.get('C', 0.0)
    heavy_rate = rates.get('T', 0.0)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Rates - ParkSmart</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&display=swap');
            body {{ background-color: #121212; color: #ffffff; font-family: -apple-system, sans-serif; padding: 40px; margin: 0; }}
            h1.main-title {{ text-align: center; font-family: 'Cinzel', serif; font-weight: 800; font-size: 3.2rem; margin-bottom: 10px; color: #ffffff; letter-spacing: 3px; }}
            .subtitle {{ display: block; font-family: sans-serif; font-size: 1rem; color: #888; letter-spacing: 4px; text-transform: uppercase; text-align: center; margin-bottom: 50px; }}

            .form-container {{ background-color: #1e1e1e; max-width: 450px; margin: 0 auto; padding: 35px; border-radius: 12px; border: 1px solid #333; }}
            .form-group {{ margin-bottom: 25px; }}
            label {{ display: block; color: #aaaaaa; margin-bottom: 10px; font-weight: bold; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1px; }}

            .input-wrapper {{ position: relative; }}
            .currency-symbol {{ position: absolute; left: 15px; top: 50%; transform: translateY(-50%); color: #00d09c; font-size: 1.2rem; font-weight: bold; }}

            input[type="number"] {{ width: 100%; padding: 15px 15px 15px 40px; background-color: #2a2a2a; border: 1px solid #444; color: white; border-radius: 6px; font-size: 1.2rem; box-sizing: border-box; font-weight: bold; }}
            input[type="number"]:focus {{ outline: none; border-color: #00d09c; }}

            .btn-save {{ width: 100%; padding: 18px; font-size: 1.2rem; font-weight: bold; border-radius: 8px; border: none; cursor: pointer; transition: 0.2s; background-color: #f39c12; color: white; margin-top: 15px; }}
            .btn-save:hover {{ background-color: #d68910; transform: translateY(-3px); }}

            .back-nav {{ text-align: center; margin-top: 40px; }}
            .back-nav a {{ color: #888; text-decoration: none; font-size: 1.1rem; }}
            .back-nav a:hover {{ color: white; }}
        </style>
    </head>
    <body>

        <h1 class="main-title">ParkSmart</h1>
        <span class="subtitle">Edit Hourly Billing Rates</span>

        <div class="form-container">
            <form id="ratesForm" onsubmit="submitRates(event)">
            
                <div class="form-group">
                    <label>🏍️ Two-Wheeler Rate / Hr</label>
                    <div class="input-wrapper">
                        <span class="currency-symbol">₹</span>
                        <input type="number" id="rate-S" step="0.5" min="0" value="{bike_rate}" required>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>🚗 Cars Rate / Hr</label>
                    <div class="input-wrapper">
                        <span class="currency-symbol">₹</span>
                        <input type="number" id="rate-C" step="0.5" min="0" value="{car_rate}" required>
                    </div>
                </div>

                <div class="form-group">
                    <label>🛻 Heavy Vehicles Rate / Hr</label>
                    <div class="input-wrapper">
                        <span class="currency-symbol">₹</span>
                        <input type="number" id="rate-T" step="0.5" min="0" value="{heavy_rate}" required>
                    </div>
                </div>

                <button type="submit" class="btn-save">💾 Update Rates</button>
            </form>
        </div>

        <div class="back-nav">
            <a href="/admin/configure">← Back to Configuration Center</a>
        </div>

        <script>
            async function submitRates(event) {{
                event.preventDefault();

                const payload = {{
                    car_rate: parseFloat(document.getElementById('rate-C').value),
                    bike_rate: parseFloat(document.getElementById('rate-S').value),
                    heavy_rate: parseFloat(document.getElementById('rate-T').value)
                }};

                const response = await fetch('/admin/configure/edit-rates', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(payload)
                }});

                if (response.ok) {{
                    alert("Billing rates successfully updated!");
                    window.location.href = '/admin/configure';
                }} else {{
                    alert("Failed to update rates. Check backend console.");
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.post("/admin/configure/edit-rates")
async def process_edit_rates(data: EditRatesSchema):
    try:
        rates_dict = {
            'S': data.bike_rate,
            'C': data.car_rate,
            'T': data.heavy_rate
        }

        parking_lot.update_rates(rates_dict)

        return {"status": "success", "message": "Rates updated successfully"}
    except Exception as e:
        print(f"ParkingLot error updating rates: {{str(e)}}")
        return {"status": "error", "message": str(e)}


@router.get("/admin/users", response_class=HTMLResponse)
async def manage_users_ui():
    users_list = db.get_all_users()

    active_logged_in_user = "admin"

    users_json = json.dumps(users_list)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>User Management - ParkSmart</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&display=swap');
            body {{ background-color: #121212; color: #ffffff; font-family: -apple-system, sans-serif; padding: 40px; margin: 0; }}
            h1.main-title {{ text-align: center; font-family: 'Cinzel', serif; font-weight: 800; font-size: 3.2rem; margin-bottom: 10px; color: #ffffff; letter-spacing: 3px; }}
            .subtitle {{ display: block; font-family: sans-serif; font-size: 1rem; color: #888; letter-spacing: 4px; text-transform: uppercase; text-align: center; margin-bottom: 50px; }}

            .container {{ max-width: 800px; margin: 0 auto; }}

            /* TABLE STYLES */
            .table-wrapper {{ background-color: #1e1e1e; border: 1px solid #333; border-radius: 12px; overflow: hidden; margin-bottom: 40px; max-height: 400px; overflow-y: auto; }}
            table {{ width: 100%; border-collapse: collapse; text-align: left; }}
            th {{ background-color: #252525; padding: 15px 20px; color: #00d09c; text-transform: uppercase; font-size: 0.9rem; letter-spacing: 1px; position: sticky; top: 0; z-index: 10; border-bottom: 1px solid #333; }}
            td {{ padding: 15px 20px; border-bottom: 1px solid #2a2a2a; color: #e0e0e0; font-size: 1.1rem; }}

            /* HOVER ROW & DELETE BUTTON MECHANIC */
            tr {{ transition: background-color 0.2s; }}
            tr:hover {{ background-color: #2a2a2a; }}

            .active-user-tag {{ color: #f39c12; font-size: 0.9rem; font-weight: bold; margin-left: 10px; }}

            .action-col {{ width: 100px; text-align: right; }}
            .delete-btn {{ opacity: 0; background-color: #e74c3c; color: white; border: none; padding: 8px 15px; border-radius: 6px; cursor: pointer; font-weight: bold; transition: opacity 0.2s, background-color 0.2s; }}
            .delete-btn:hover {{ background-color: #c0392b; }}

            /* The magic trick: When row is hovered, show the delete button inside it */
            tr:hover .delete-btn {{ opacity: 1; }}

            /* ADD USER FORM STYLES */
            .form-box {{ background-color: #1e1e1e; padding: 30px; border-radius: 12px; border: 1px solid #333; }}
            .form-box h3 {{ margin-top: 0; color: #3498db; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #333; padding-bottom: 15px; margin-bottom: 25px; }}

            .input-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 25px; }}
            .form-group label {{ display: block; color: #aaaaaa; margin-bottom: 8px; font-weight: bold; font-size: 0.9rem; text-transform: uppercase; }}
            .form-group input, .form-group select {{ width: 100%; padding: 12px; background-color: #2a2a2a; border: 1px solid #444; color: white; border-radius: 6px; font-size: 1.1rem; box-sizing: border-box; }}

            .btn-add {{ width: 100%; padding: 15px; font-size: 1.2rem; font-weight: bold; border-radius: 8px; border: none; cursor: pointer; background-color: #27ae60; color: white; transition: 0.2s; }}
            .btn-add:hover {{ background-color: #219653; }}

            .back-nav {{ text-align: center; margin-top: 40px; }}
            .back-nav a {{ color: #888; text-decoration: none; font-size: 1.1rem; }}
            .back-nav a:hover {{ color: white; }}
        </style>
    </head>
    <body>

        <h1 class="main-title">ParkSmart</h1>
        <span class="subtitle">System User Management</span>

        <div class="container">

            <!-- 1. THE USERS TABLE -->
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Username</th>
                            <th>Role</th>
                            <th class="action-col">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="userTableBody">
                        <!-- Populated by JS -->
                    </tbody>
                </table>
            </div>

            <!-- 2. THE ADD USER FORM -->
            <div class="form-box">
                <h3>➕ Create New Account</h3>
                <form id="addUserForm" onsubmit="addUser(event)">
                    <div class="input-grid">
                        <div class="form-group">
                            <label>Username</label>
                            <input type="text" id="newUsername" required>
                        </div>
                        <div class="form-group">
                            <label>Password</label>
                            <input type="password" id="newPassword" required>
                        </div>
                        <div class="form-group">
                            <label>Role</label>
                            <select id="newRole">
                                <option value="admin">Admin</option>
                                <option value="operator">Operator</option>
                            </select>
                        </div>
                    </div>
                    <button type="submit" class="btn-add">Create Account</button>
                </form>
            </div>

        </div>

        <div class="back-nav">
            <a href="/admin/dashboard">← Back to Dashboard</a>
        </div>

        <script>
            let usersData = {users_json};
            const activeUser = "{active_logged_in_user}";

            // RENDER TABLE DYNAMICALLY
            function renderTable() {{
                const tbody = document.getElementById('userTableBody');
                tbody.innerHTML = '';

                usersData.forEach(user => {{
                    const isMe = (user.username === activeUser);

                    const tr = document.createElement('tr');
                    tr.id = `user-row-${{user.user_id}}`;

                    tr.innerHTML = `
                        <td>
                            ${{user.username}} 
                            ${{isMe ? '<span class="active-user-tag">(You)</span>' : ''}}
                        </td>
                        <td>${{user.role.toUpperCase()}}</td>
                        <td class="action-col">
                            ${{!isMe ? `<button class="delete-btn" onclick="deleteUser(${{user.user_id}}, '${{user.username}}')">🗑️ Delete</button>` : ''}}
                        </td>
                    `;
                    tbody.appendChild(tr);
                }});
            }}

            // ADD USER LOGIC
            async function addUser(event) {{
                event.preventDefault();

                const username = document.getElementById('newUsername').value;
                const password = document.getElementById('newPassword').value;
                const role = document.getElementById('newRole').value;

                const response = await fetch('/admin/users/add', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ username, password, role }})
                }});

                const result = await response.json();

                if (response.ok && result.status === 'success') {{
                    document.getElementById('addUserForm').reset();
                    window.location.reload();
                }} else {{
                    alert("Error adding user: " + (result.message || "Username may already exist."));
                }}
            }}

            // DELETE USER LOGIC
            async function deleteUser(userId, username) {{
                if (!confirm(`Are you sure you want to permanently delete the account for '${{username}}'?`)) return;

                const response = await fetch(`/admin/users/remove/${{userId}}`, {{
                    method: 'DELETE'
                }});

                if (response.ok) {{
                    document.getElementById(`user-row-${{userId}}`).remove();
                    usersData = usersData.filter(u => u.user_id !== userId);
                }} else {{
                    alert("Failed to delete user. Check backend console.");
                }}
            }}

            renderTable();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.post("/admin/users/add")
async def process_add_user(data: AddUserSchema):
    success = db.add_new_user(data.username, data.password, data.role)
    if success:
        return {"status": "success", "message": "User created."}
    else:
        raise HTTPException(status_code=400, detail="Username already exists or database error.")


@router.delete("/admin/users/remove/{user_id}")
async def process_delete_user(user_id: int):
    try:
        db.delete_user(user_id)
        return {"status": "success", "message": "User deleted."}
    except Exception as e:
        print(f"Database error deleting user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
