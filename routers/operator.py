import os
from dotenv import load_dotenv
import httpx
import requests
from pydantic import BaseModel
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from datetime import datetime

from core.ParkingLot import ParkingLot
from db.Database import Database
from interface.OperatorTerminal import OperatorTerminal

# ---------------------------------------------------------
# INITIALIZATION & SCHEMAS
# ---------------------------------------------------------
router = APIRouter()
db = Database()
parking_lot = ParkingLot(db)
backend_terminal = OperatorTerminal()
load_dotenv()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
PLATE_FILE = os.path.join(PROJECT_ROOT, "latest_plate.txt")
EXIT_PLATE_FILE = os.path.join(PROJECT_ROOT, "latest_exit_plate.txt")

class VehicleEntrySchema(BaseModel):
    v_plate: str
    v_type: str

class VehicleExitSchema(BaseModel):
    search_query: str


# ---------------------------------------------------------
# 1. MAIN OPERATOR DASHBOARD UI
# ---------------------------------------------------------
@router.get("/operator/dashboard", response_class=HTMLResponse)
async def operator_dashboard():
    stats = parking_lot.get_stats()

    total_spots = parking_lot.get_total_spots_count()
    available_spots = sum(data[0] for data in stats.values())
    occupied_spots = total_spots - available_spots

    today_str = datetime.now().strftime("%Y-%m-%d")
    try:
        parking_lot.cursor.execute("""
                                   SELECT COUNT(*), SUM(fee)
                                   FROM session_logs
                                   WHERE exit_time LIKE ?
                                   """, (f"{today_str}%",))

        daily_data = parking_lot.cursor.fetchone()
        todays_exits = daily_data[0] if daily_data and daily_data[0] else 0
        todays_revenue = daily_data[1] if daily_data and daily_data[1] else 0
    except Exception as e:
        print(f"Error fetching financial stats: {e}")
        todays_exits = 0
        todays_revenue = 0

    html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Operator Dashboard - ParkSmart</title>
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&display=swap');

                    body {{
                        background-color: #121212;
                        color: #ffffff;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        margin: 0;
                        padding: 50px;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                    }}

                    /* TITLE STYLES */
                    h1.main-title {{ 
                        text-align: center; 
                        margin-bottom: 5px; 
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
                        margin-bottom: 40px;
                        letter-spacing: 6px;
                        text-transform: uppercase;
                        text-align: center;
                    }}

                    .dashboard-container {{ width: 100%; max-width: 1100px; }}

                    /* LIVE STATS UI */
                    .stats-container {{ display: flex; justify-content: space-between; background-color: #1e1e1e; padding: 20px 30px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #333; }}
                    .stat-box h3 {{ margin: 0; color: #e0e0e0; font-size: 1.15rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
                    .stat-box h1 {{ margin: 5px 0 5px 0; font-size: 2.5rem; color: #ffffff; }}
                    .stat-box p {{ margin: 5px 0 0 0; font-size: 1rem; color: #cccccc; font-weight: 500; word-spacing: 2px; }}

                    /* FINANCIAL BANNER */
                    .financial-banner {{ 
                        display: flex; 
                        justify-content: space-around; 
                        background-color: #1a1a1a; 
                        padding: 20px; 
                        border-radius: 12px; 
                        margin-bottom: 30px; 
                        border: 1px solid #22c55e;
                        box-shadow: 0 4px 15px rgba(34, 197, 94, 0.1);
                    }}
                    .fin-box {{ text-align: center; width: 45%; }}
                    .fin-box p {{ color: #888; font-size: 0.9rem; text-transform: uppercase; margin: 0 0 5px 0; letter-spacing: 1px; font-weight: bold; }}
                    .fin-box h2 {{ margin: 0; font-size: 2.2rem; }}
                    .divider {{ width: 1px; background-color: #333; }}

                    /* MAP DROPDOWN */
                    details {{ background-color: #1e1e1e; border: 1px solid #333; border-radius: 12px; margin-bottom: 30px; overflow: hidden; }}
                    summary {{ padding: 20px; font-size: 1.2rem; font-weight: bold; cursor: pointer; list-style: none; text-align: center; background-color: #2a2a2a; transition: background 0.2s; }}
                    summary:hover {{ background-color: #333; }}

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
                    .spot-type-C {{ color: #22c55e; }}
                    .spot-type-T {{ color: #f97316; }}

                    /* Status Styles - Softer empty spots, bold occupied spots */
                    .spot-free {{ border: 1px solid currentcolor; opacity: 0.4; background-color: transparent; }}
                    .spot-occupied {{ border: 2px solid currentcolor; background-color: #1a1a1a; color: #fff; box-shadow: 0 4px 10px rgba(0,0,0,0.4); opacity: 1; }}
                    .plate-badge {{ background-color: #fff; color: #000; padding: 3px 6px; border-radius: 4px; font-size: 13px; margin-top: 5px; display: inline-block; box-shadow: inset 0 0 5px rgba(0,0,0,0.2); }}

                    /* OPERATOR ACTIONS */
                    .action-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 20px; }}
                    .btn-action {{ display: block; text-align: center; color: white; text-decoration: none; padding: 20px; border-radius: 12px; font-size: 1.2rem; font-weight: bold; transition: transform 0.2s, background 0.2s; border: none; cursor: pointer; }}
                    .btn-action:hover {{ transform: translateY(-5px); }}

                    .btn-entry {{ background-color: #27ae60; }}
                    .btn-entry:hover {{ background-color: #219653; }}

                    .btn-exit {{ background-color: #2980b9; }}
                    .btn-exit:hover {{ background-color: #1f618d; }}

                    .btn-search {{ background-color: #f39c12; }}
                    .btn-search:hover {{ background-color: #d68910; }}

                    /* LOGOUT BUTTON */
                    .logout-btn {{ display: block; width: 200px; margin: 0 auto; text-align: center; background-color: transparent; color: #e74c3c; text-decoration: none; padding: 15px; border: 2px solid #e74c3c; border-radius: 8px; font-weight: bold; transition: all 0.2s; }}
                    .logout-btn:hover {{ background-color: #e74c3c; color: white; }}
                </style>
            </head>
            <body>
                <h1 class="main-title">ParkSmart<span class="subtitle">Operator Dashboard</span></h1>

                <div class="dashboard-container">
                    <!-- LIVE TRACKER -->
                    <div class="stats-container">
                        <div class="stat-box">
                            <h3 style="color: #00d09c;">Available Spots</h3>
                            <h1>{available_spots}</h1>
                            <p>Two-Wheeler: {stats.get('S', (0, 0))[0]} | Car: {stats.get('C', (0, 0))[0]} | Heavy: {stats.get('T', (0, 0))[0]}</p>
                        </div>
                        <div class="stat-box occupied" style="text-align: center;">
                            <h3 style="color: #e74c3c;">Occupied</h3>
                            <h1>{occupied_spots}</h1>
                            <p>Two-Wheeler: {stats.get('S', (0, 0))[1] - stats.get('S', (0, 0))[0]} | Car: {stats.get('C', (0, 0))[1] - stats.get('C', (0, 0))[0]} | Heavy: {stats.get('T', (0, 0))[1] - stats.get('T', (0, 0))[0]}</p>
                        </div>
                        <div class="stat-box" style="text-align: right;">
                            <h3 style="color: #3498db;">Total Capacity</h3>
                            <h1 style="color: white;">{total_spots}</h1>
                            <p>Two-Wheeler: {stats.get('S', (0, 0))[1]} | Car: {stats.get('C', (0, 0))[1]} | Heavy: {stats.get('T', (0, 0))[1]}</p>
                        </div>
                    </div>

                    <!-- FINANCIAL BANNER -->
                    <div class="financial-banner">
                        <div class="fin-box">
                            <p>Today's Completed Exits</p>
                            <h2 style="color: #3b82f6;">{todays_exits}</h2>
                        </div>
                        <div class="divider"></div>
                        <div class="fin-box">
                            <p>Today's Revenue Collected</p>
                            <h2 style="color: #22c55e;">₹{todays_revenue}</h2>
                        </div>
                    </div>

                    <!-- LIVE MAP DROPDOWN -->
                    <details>
                        <summary>🗺️ View Live Parking Map</summary>
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

                    <!-- OPERATOR ACTIONS -->
                    <div class="action-grid">
                        <a href="/operator/entry" class="btn-action btn-entry">🟢 Entry Vehicle</a>
                        <a href="/operator/exit" class="btn-action btn-exit">🔴 Exit Vehicle</a>
                        <a href="/operator/search" class="btn-action btn-search">🔍 Search Vehicle</a>
                    </div>

                    <!-- LOGOUT -->
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

                                // Reveal Controls and default to first floor
                                controls.style.display = 'flex';
                                if (firstFloor !== null) {{
                                    document.getElementById('floor-view-' + firstFloor).style.display = 'block';
                                }}

                                // Listen for dropdown changes
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


# ---------------------------------------------------------
# 2. VEHICLE ENTRY UI
# ---------------------------------------------------------
@router.get("/operator/entry", response_class=HTMLResponse)
async def operator_entry_ui():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Vehicle Entry - ParkSmart</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&display=swap');

            body { 
                background-color: #121212; 
                color: #ffffff; 
                font-family: -apple-system, sans-serif; 
                margin: 0; 
                padding: 40px; }

            h1.main-title { 
                text-align: center; 
                margin-bottom: 5px; 
                font-family: 'Cinzel', serif; 
                font-weight: 800; 
                font-size: 3.2rem; 
                letter-spacing: 4px; }
                
            .subtitle { 
                display: block; 
                font-family: sans-serif; 
                font-size: 1rem; 
                color: #888; 
                letter-spacing: 4px; 
                text-transform: uppercase; 
                text-align: center; 
                margin-bottom: 40px; }

            .dashboard-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; max-width: 1200px; margin: 0 auto; }

            /* LEFT COLUMN: CAMERA */
            .camera-container { background-color: #1e1e1e; border: 1px solid #333; border-radius: 12px; padding: 20px; text-align: center; }
            .camera-container h3 { color: #00d09c; margin-top: 0; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px; }
            .live-feed { width: 100%; border-radius: 8px; border: 1px solid #444; aspect-ratio: 16/9; background-color: #000; object-fit: cover; }

            /* RIGHT COLUMN: ACTION PANEL */
            .action-container { background-color: #1e1e1e; border: 1px solid #333; border-radius: 12px; padding: 30px; display: flex; flex-direction: column; justify-content: center; }

            /* Phase 1: Input Form */
            #input-phase { display: block; }
            .form-group { margin-bottom: 30px; }
            .form-group label { display: block; color: #aaaaaa; margin-bottom: 10px; font-weight: bold; font-size: 1rem; text-transform: uppercase; letter-spacing: 1px; }

            input[type="text"] { width: 100%; padding: 18px; background-color: #2a2a2a; border: 2px solid #444; color: white; border-radius: 8px; font-size: 2rem; font-weight: bold; text-align: center; text-transform: uppercase; box-sizing: border-box; letter-spacing: 2px; transition: border-color 0.2s; }
            input[type="text"]:focus { outline: none; border-color: #3498db; }

            .vtype-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
            .vtype-btn { background-color: #2a2a2a; color: #888; border: 2px solid #444; padding: 20px 10px; border-radius: 8px; font-size: 1.1rem; font-weight: bold; cursor: pointer; transition: all 0.2s; }
            .vtype-btn:hover { background-color: #333; color: white; }
            .vtype-btn.active { background-color: #3498db; color: white; border-color: #3498db; }

            .btn-confirm { width: 100%; background-color: #27ae60; color: white; padding: 20px; border: none; border-radius: 8px; font-size: 1.3rem; font-weight: bold; cursor: pointer; margin-top: 20px; transition: background 0.2s; }
            .btn-confirm:hover { background-color: #219653; }

            /* Phase 2: Success State */
            #success-phase { display: none; text-align: center; }
            .success-icon { font-size: 4rem; margin-bottom: 10px; }
            .success-title { color: #00d09c; font-size: 1.5rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 20px; }
            .spot-id-display { background-color: #2a2a2a; border: 2px dashed #00d09c; border-radius: 12px; padding: 30px; font-size: 4.5rem; font-weight: 800; color: white; margin-bottom: 20px; letter-spacing: 4px; }
            .entry-time-display { color: #aaaaaa; font-size: 1.2rem; margin-bottom: 30px; }

            .btn-next { width: 100%; background-color: #3498db; color: white; padding: 20px; border: none; border-radius: 8px; font-size: 1.2rem; font-weight: bold; cursor: pointer; transition: background 0.2s; }
            .btn-next:hover { background-color: #2980b9; }

            .back-nav { text-align: center; margin-top: 40px; }
            .back-nav a { color: #888; text-decoration: none; font-size: 1.1rem; }
            .back-nav a:hover { color: white; }
        </style>
    </head>
    <body>
        <h1 class="main-title">ParkSmart</h1>
        <span class="subtitle">Gate Entry Operations</span>

        <div class="dashboard-grid">
            <!-- LEFT: CAMERA FEED (Pointed to secure proxy route) -->
            <div class="camera-container">
                <h3>🔴 Live ANPR Feed</h3>
                <img src="/operator/api/camera-stream" class="live-feed" alt="Camera Feed Offline">
            </div>

            <!-- RIGHT: ACTION PANEL -->
            <div class="action-container">
                <!-- PHASE 1: INPUT -->
                <div id="input-phase">
                    <div class="form-group">
                        <label>Detected License Plate</label>
                        <input type="text" id="plateInput" placeholder="AWAITING SCAN...">
                    </div>

                    <div class="form-group">
                        <label>Vehicle Type</label>
                        <div class="vtype-grid">
                            <button class="vtype-btn active" onclick="selectType('S')" id="btn-S">Two-Wheeler (S)</button>
                            <button class="vtype-btn" onclick="selectType('C')" id="btn-C">Car (C)</button>
                            <button class="vtype-btn" onclick="selectType('T')" id="btn-T">Heavy (T)</button>
                        </div>
                    </div>
                    <button class="btn-confirm" onclick="submitEntry()">✅ Confirm Entry</button>
                </div>

                <!-- PHASE 2: SUCCESS -->
                <div id="success-phase">
                    <div class="success-icon">✅</div>
                    <div class="success-title">Spot Allocated</div>
                    <div class="spot-id-display" id="displaySpotId">0-S-1</div>
                    <div class="entry-time-display" id="displayEntryTime">Time of Entry: -</div>
                    <button class="btn-next" onclick="resetForm()">Scan Next Vehicle ➔</button>
                </div>
            </div>
        </div>

        <div class="back-nav">
            <a href="/operator/dashboard">← Back to Dashboard</a>
        </div>

        <script>
            let selectedType = 'S';
            let lastFetchedPlate = "";

            function selectType(type) {
                selectedType = type;
                document.querySelectorAll('.vtype-btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById('btn-' + type).classList.add('active');
            }

            setInterval(async () => {
                if (document.getElementById('input-phase').style.display === 'none') return;
                try {
                    const response = await fetch('/operator/api/latest-plate');
                    if (response.ok) {
                        const data = await response.json();
                        if (data.plate && data.plate !== lastFetchedPlate) {
                            document.getElementById('plateInput').value = data.plate;
                            lastFetchedPlate = data.plate;
                        }
                    }
                } catch (e) { console.log("Waiting for ANPR script..."); }
            }, 1000);

            async function submitEntry() {
                const plate = document.getElementById('plateInput').value.trim();
                if (!plate) {
                    alert("Please enter a valid License Plate.");
                    return;
                }
                const response = await fetch('/operator/api/process-entry', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ v_plate: plate, v_type: selectedType })
                });

                const result = await response.json();

                if (response.ok && result.status === 'success') {
                    document.getElementById('displaySpotId').innerText = result.spot_id;
                    document.getElementById('displayEntryTime').innerText = `Time of Entry: ${result.entry_time}`;
                    document.getElementById('input-phase').style.display = 'none';
                    document.getElementById('success-phase').style.display = 'block';
                } else {
                    alert("Error: " + (result.message || "Failed to process entry."));
                }
            }

            function resetForm() {
                document.getElementById('plateInput').value = '';
                lastFetchedPlate = ''; 
                document.getElementById('success-phase').style.display = 'none';
                document.getElementById('input-phase').style.display = 'block';
            }
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ---------------------------------------------------------
# 2.5. BACKGROUND API ROUTES
# ---------------------------------------------------------
@router.get("/operator/api/camera-stream")
def proxy_camera_stream():
    CAMERA_URL = os.getenv("CAMERA_URL", "http://YOUR_CAMERA_IP:8080/video")
    USERNAME = os.getenv("CAMERA_USER", "YOUR_USERNAME")
    PASSWORD = os.getenv("CAMERA_PASS", "YOUR_PASSWORD")

    try:
        req = requests.get(
            CAMERA_URL,
            auth=(USERNAME, PASSWORD),
            stream=True,
            timeout=10,
            proxies={"http": None, "https": None}
        )

        actual_content_type = req.headers.get("Content-Type", "multipart/x-mixed-replace; boundary=BaSe64")
        req.close()

    except Exception:
        actual_content_type = "multipart/x-mixed-replace; boundary=BaSe64"

    async def iter_camera():
        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                async with client.stream("GET", CAMERA_URL, auth=(USERNAME, PASSWORD), timeout=30.0) as response:
                    async for chunk in response.aiter_bytes(chunk_size=4096):
                        if chunk:
                            yield chunk
            except Exception as e:
                print(f"Stream interrupted (Auto-recovering): {str(e)}")

    return StreamingResponse(iter_camera(), media_type=actual_content_type)


@router.get("/operator/api/latest-plate")
async def get_latest_plate():
    try:
        if os.path.exists(PLATE_FILE):
            with open(PLATE_FILE, "r") as f:
                plate = f.read().strip()
            return {"plate": plate}
    except Exception:
        pass
    return {"plate": ""}


@router.post("/operator/api/process-entry")
async def process_entry(data: VehicleEntrySchema):
    try:
        result = OperatorTerminal.process_web_arrival(data.v_type, data.v_plate)

        if result["status"] == "success":
            if os.path.exists(PLATE_FILE):
                with open(PLATE_FILE, "w") as f:
                    f.write("")
            return JSONResponse(content=result)
        else:
            return JSONResponse(status_code=400, content=result)

    except Exception as e:
        print(f"Backend error processing entry: {str(e)}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Server error processing entry."})


# ---------------------------------------------------------
# 3. VEHICLE EXIT UI
# ---------------------------------------------------------
@router.get("/operator/exit", response_class=HTMLResponse)
async def operator_exit_ui():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ParkSmart - Gate Exit Operations</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&display=swap');

            body { 
                background-color: #121212; 
                color: #ffffff; 
                font-family: -apple-system, sans-serif; 
                margin: 0; 
                padding: 40px; 
                display: flex;
                flex-direction: column;
                align-items: center;
            }

            h1.main-title { 
                text-align: center; 
                margin-bottom: 5px; 
                font-family: 'Cinzel', serif; 
                font-weight: 800; 
                font-size: 3.2rem; 
                letter-spacing: 4px; 
            }
            .subtitle { 
                display: block; 
                font-family: sans-serif; 
                font-size: 1rem; 
                color: #888; 
                letter-spacing: 4px; 
                text-transform: uppercase; 
                text-align: center; 
                margin-bottom: 40px; 
            }

            /* Layout Containers (Updated to Match Entry) */
            .dashboard-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; max-width: 1200px; margin: 0 auto; width: 100%; }

            .camera-container { 
                background-color: #1e1e1e; 
                border: 1px solid #333; 
                border-radius: 12px; 
                padding: 20px; 
                text-align: center; 
                height: fit-content;
            }
            .camera-container h3 { color: #22c55e; margin-top: 0; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px; }
            .live-feed { width: 100%; border-radius: 8px; border: 1px solid #444; aspect-ratio: 16/9; background-color: #000; object-fit: cover; }

            .card { 
                background-color: #222222; 
                border-radius: 12px; 
                padding: 24px; 
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
            }

            /* Inputs & Search */
            .search-bar { display: flex; gap: 15px; margin-bottom: 10px; }
            input[type="text"] { 
                flex: 1; 
                padding: 16px; 
                border-radius: 8px; 
                border: 1px solid #333333; 
                background-color: #1a1a1a; 
                color: #ffffff; 
                font-size: 16px; 
                font-weight: bold;
                outline: none;
                transition: border-color 0.2s;
                text-transform: uppercase;
            }
            input[type="text"]:focus { border-color: #555555; }
            input[type="text"]::placeholder { color: #666666; font-weight: normal; }

            .error-message { color: #ef4444; font-size: 14px; font-weight: bold; margin-bottom: 20px; display: none; }

            /* Buttons */
            button { 
                padding: 16px 24px; 
                border: none; 
                border-radius: 8px; 
                font-weight: bold; 
                cursor: pointer; 
                transition: opacity 0.2s; 
                font-size: 16px; 
            }
            button:hover { opacity: 0.85; }

            .btn-search { background-color: #22c55e; color: white; }
            .btn-success { background-color: #22c55e; color: white; width: 100%; font-size: 18px; margin-top: 15px; }
            .btn-cancel { background-color: transparent; border: 1px solid #444; color: #a0a0a0; width: 100%; margin-top: 10px; }
            .btn-action { background-color: #333333; color: white; padding: 8px 16px; font-size: 14px; border-radius: 6px; }

            /* Section Headers inside Cards */
            .section-label { font-size: 11px; text-transform: uppercase; color: #888888; font-weight: bold; letter-spacing: 1px; margin-bottom: 12px; display: block; }

            /* Sleek Table Design */
            table { width: 100%; border-collapse: collapse; }
            th { text-align: left; padding: 16px 12px; border-bottom: 1px solid #333333; color: #888888; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
            td { padding: 16px 12px; border-bottom: 1px solid #2a2a2a; font-size: 15px; }
            tr:last-child td { border-bottom: none; }
            tr:hover td { background-color: #2a2a2a; }

            /* Summary Grid for Checkout */
            .summary-card { background-color: #1a1a1a; border: 1px solid #333333; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
            .summary-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 15px; }
            .summary-item { display: flex; flex-direction: column; gap: 4px; }
            .summary-item span.label { color: #888888; font-size: 12px; text-transform: uppercase; }
            .summary-item span.value { font-weight: bold; color: #ffffff; font-size: 16px; text-transform: uppercase; }
            .highlight-fee { color: #22c55e !important; font-size: 24px !important; }

            /* Links */
            .bottom-link { color: #666666; text-decoration: none; font-size: 14px; transition: color 0.2s; display: block; margin-top: 40px; text-align: center; }
            .bottom-link:hover { color: #ffffff; }

        </style>
    </head>
    <body>
        <div class="header-title">
            <h1 class="main-title">ParkSmart</h1>
            <span class="subtitle">Gate Exit Operations</span>
        </div>

        <div class="dashboard-grid">
            <!-- LEFT: CAMERA FEED -->
            <div class="camera-container">
                <h3>🔴 Live Exit Camera</h3>
                <img src="/operator/api/camera-stream" class="live-feed" alt="Camera Feed Offline">
            </div>

            <!-- RIGHT: ACTION PANEL -->
            <div class="card">
                <span class="section-label">Look Up Vehicle</span>
                <div class="search-bar">
                    <input type="text" id="exitSearchInput" placeholder="AWAITING SCAN OR TYPE...">
                    <button class="btn-search" onclick="triggerLookup()">Search</button>
                </div>

                <!-- NEW: Inline Error Message -->
                <div id="lookupError" class="error-message"></div>

                <!-- Checkout Summary Card (Hidden by default) -->
                <div id="checkoutCard" style="display: none;">
                    <span class="section-label" style="color: #22c55e;">Confirm Checkout Data</span>
                    <div class="summary-card">
                        <div class="summary-grid">
                            <div class="summary-item"><span class="label">Detected Plate</span><span class="value" id="sumPlate"></span></div>
                            <div class="summary-item"><span class="label">Spot ID</span><span class="value" id="sumSpot"></span></div>
                            <div class="summary-item"><span class="label">Time of Entry</span><span class="value" id="sumEntry"></span></div>
                            <div class="summary-item"><span class="label">Vehicle Type</span><span class="value" id="sumType"></span></div>
                            <div class="summary-item"><span class="label">Total Duration</span><span class="value" id="sumDuration"></span></div>
                            <div class="summary-item"><span class="label">Total Due</span><span class="value highlight-fee" id="sumFee"></span></div>
                        </div>
                    </div>
                    <button class="btn-success" onclick="finalizeCheckout()">☑ Generate Bill & Checkout</button>
                    <button class="btn-cancel" onclick="cancelCheckout()">Cancel</button>
                </div>

                <!-- Live Table -->
                <div id="tableContainer">
                    <span class="section-label" style="margin-top: 15px;">Active Sessions Database</span>
                    <table>
                        <thead>
                            <tr>
                                <th>License Plate</th>
                                <th>Spot ID</th>
                                <th>Entry Time</th>
                                <th>Type</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody id="sessionsBody">
                            <!-- JS Populates Rows Here -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <a href="/operator/dashboard" class="bottom-link">&larr; Back to Dashboard</a>

        <script>
            // 1. Fetch data on load
            async function loadActiveSessions() {
                try {
                    const response = await fetch('/operator/api/active-sessions');
                    const data = await response.json();

                    if (data.status === 'success') {
                        const tbody = document.getElementById('sessionsBody');
                        tbody.innerHTML = ''; 

                        data.sessions.forEach(session => {
                            let spotColor = '#3b82f6';
                            if (session.type === 'C') spotColor = '#22c55e';
                            else if (session.type === 'T') spotColor = '#f97316';

                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td style="font-weight: bold; text-transform: uppercase;">${session.plate}</td>
                                <td style="color: ${spotColor}; font-weight: bold; text-transform: uppercase;">${session.spot}</td>
                                <td style="color: #a0a0a0;">${session.entry}</td>
                                <td style="color: #a0a0a0;">${session.type}</td>
                                <td><button class="btn-action" onclick="lookupFromTable('${session.plate}')">Select</button></td>
                            `;
                            tbody.appendChild(row);
                        });
                    }
                } catch (error) {
                    console.error("Failed to load sessions:", error);
                }
            }

            // 2. Live Typing Filter
            document.getElementById('exitSearchInput').addEventListener('input', function(e) {
                const searchString = e.target.value.toUpperCase();
                const rows = document.querySelectorAll('#sessionsBody tr');

                rows.forEach(row => {
                    const plate = row.cells[0].textContent.toUpperCase();
                    const spot = row.cells[1].textContent.toUpperCase();
                    row.style.display = (plate.includes(searchString) || spot.includes(searchString)) ? '' : 'none';
                });
            });

            let currentCheckoutQuery = ""; 
            let lastAutoPlate = ""; // Tracks the last plate the AI searched for to prevent spam

            // 3. Step 1: Lookup
            function lookupFromTable(query) {
                document.getElementById('exitSearchInput').value = query.toUpperCase();
                triggerLookup();
            }

            async function triggerLookup() {
                const query = document.getElementById('exitSearchInput').value.trim();
                const errorDiv = document.getElementById('lookupError');
                errorDiv.style.display = 'none'; // Clear old errors

                if (!query) {
                    errorDiv.innerText = "Please enter a Plate or Spot ID!";
                    errorDiv.style.display = 'block';
                    return;
                }

                try {
                    const response = await fetch('/operator/api/lookup-vehicle', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ search_query: query })
                    });
                    const result = await response.json();

                    if (result.status === 'success') {
                        document.getElementById('sumPlate').innerText = result.plate;

                        const sumSpotElement = document.getElementById('sumSpot');
                        sumSpotElement.innerText = result.spot;
                        if (result.type === 'C') sumSpotElement.style.color = '#22c55e';
                        else if (result.type === 'T') sumSpotElement.style.color = '#f97316';
                        else sumSpotElement.style.color = '#3b82f6';

                        document.getElementById('sumEntry').innerText = result.entry;
                        document.getElementById('sumDuration').innerText = result.duration;
                        document.getElementById('sumType').innerText = result.type === 'S' ? 'Two-Wheeler (S)' : result.type === 'C' ? 'Car (C)' : 'Heavy (T)';
                        document.getElementById('sumFee').innerText = '₹' + result.fee;

                        currentCheckoutQuery = query; 

                        document.getElementById('tableContainer').style.display = 'none';
                        document.getElementById('checkoutCard').style.display = 'block';
                    } else {
                        // NEW: Show error inline instead of blocking the screen with an alert
                        errorDiv.innerText = result.message;
                        errorDiv.style.display = 'block';
                    }
                } catch (error) {
                    errorDiv.innerText = "Error connecting to server.";
                    errorDiv.style.display = 'block';
                }
            }

            // 4. Step 2: Finalize
            async function finalizeCheckout() {
                try {
                    const response = await fetch('/operator/api/checkout-vehicle', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ search_query: currentCheckoutQuery })
                    });
                    const result = await response.json();

                    if (result.status === 'success') {
                        alert(`✅ Checkout Successful!\\nPlate: ${result.plate.toUpperCase()}\\nTotal Fee: ₹${result.fee}\\nDuration: ${result.duration}`);
                        cancelCheckout();
                        loadActiveSessions(); 
                    } else {
                        alert("Checkout Failed: " + result.message);
                    }
                } catch (error) {
                    alert("Error finalizing checkout.");
                }
            }

            function cancelCheckout() {
                document.getElementById('exitSearchInput').value = '';
                document.getElementById('checkoutCard').style.display = 'none';
                document.getElementById('lookupError').style.display = 'none';
                document.getElementById('tableContainer').style.display = 'block';
                lastAutoPlate = ""; // Reset memory on cancel

                const rows = document.querySelectorAll('#sessionsBody tr');
                rows.forEach(row => row.style.display = '');
            }

            document.addEventListener('DOMContentLoaded', loadActiveSessions);

            // 5. Live Camera Feed for Exit Gate (Updated)
            setInterval(async () => {
                const searchInput = document.getElementById('exitSearchInput');

                // NEW: Do NOT interrupt if the user is actively typing in the box!
                if (document.activeElement === searchInput) return;

                if (document.getElementById('checkoutCard').style.display === 'none') {
                    try {
                        const response = await fetch('/operator/api/latest-exit-plate');
                        const data = await response.json();

                        // NEW: Only trigger if the plate is new, preventing infinite loops on bad reads
                        if (data.plate && data.plate !== "" && data.plate !== lastAutoPlate) {
                            lastAutoPlate = data.plate; 
                            if (searchInput.value !== data.plate) {
                                searchInput.value = data.plate;
                                triggerLookup();
                            }
                        }
                    } catch (error) {}
                }
            }, 1000); 
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ---------------------------------------------------------
# 3.5.0 API ROUTE: Step 1 - Lookup Vehicle (Pre-Checkout)
# ---------------------------------------------------------
@router.post("/operator/api/lookup-vehicle")
async def lookup_vehicle(data: VehicleExitSchema):
    try:
        # Calls the safe lookup function that doesn't delete the session
        result = OperatorTerminal.process_web_exit_lookup(data.search_query)

        if result.get("status") == "success":
            return JSONResponse(content=result)
        else:
            return JSONResponse(status_code=404, content=result)

    except Exception as e:
        print(f"Backend error during lookup: {str(e)}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Server error during lookup."})


# ---------------------------------------------------------
# 3.5.1 API ROUTE: Step 2 - Finalize Checkout & Bill
# ---------------------------------------------------------
@router.post("/operator/api/checkout-vehicle")
async def checkout_vehicle(data: VehicleExitSchema):
    try:
        # Calls the final checkout function to remove the vehicle and log the exit
        result = OperatorTerminal.process_web_exit_checkout(data.search_query)

        if result.get("status") == "success":
            if os.path.exists(EXIT_PLATE_FILE):
                with open(EXIT_PLATE_FILE, "w") as f:
                    f.write("")
            return JSONResponse(content=result)
        else:
            return JSONResponse(status_code=400, content=result)

    except Exception as e:
        print(f"Backend error during checkout: {str(e)}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Server error during checkout."})


# ---------------------------------------------------------
# 3.5.2 API ROUTE: Fetch all active sessions for the Live Table
# ---------------------------------------------------------
@router.get("/operator/api/active-sessions")
async def get_active_sessions():
    try:
        parking_lot.cursor.execute("""
            SELECT plate_no, spot_id, entry_time, v_type
            FROM active_sessions
            ORDER BY entry_time DESC
        """)
        sessions = parking_lot.cursor.fetchall()

        data = [{"plate": s[0], "spot": s[1], "entry": s[2], "type": s[3]} for s in sessions]
        return JSONResponse(content={"status": "success", "sessions": data})

    except Exception as e:
        print(f"Error fetching sessions: {str(e)}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Could not load sessions."})


# ---------------------------------------------------------
# 3.5.3 API ROUTE: Get Latest Exit Plate from Exit Camera
# ---------------------------------------------------------
@router.get("/operator/api/latest-exit-plate")
async def get_latest_exit_plate():
    try:
        if os.path.exists(EXIT_PLATE_FILE):
            with open(EXIT_PLATE_FILE, "r") as f:
                plate = f.read().strip()
            return {"plate": plate}
    except Exception:
        pass
    return {"plate": ""}


# ---------------------------------------------------------
# 4. SEARCH FOR VEHICLE
# ---------------------------------------------------------
@router.get("/operator/search", response_class=HTMLResponse)
async def operator_search_ui():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ParkSmart - Search Vehicle</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&display=swap');

            body { 
                background-color: #121212; 
                color: #ffffff; 
                font-family: -apple-system, sans-serif; 
                margin: 0; 
                padding: 40px; 
                display: flex;
                flex-direction: column;
                align-items: center;
            }

            h1.main-title { 
                text-align: center; 
                margin-bottom: 5px; 
                font-family: 'Cinzel', serif; 
                font-weight: 800; 
                font-size: 3.2rem; 
                letter-spacing: 4px; 
            }
            .subtitle { 
                display: block; 
                font-family: sans-serif; 
                font-size: 1rem; 
                color: #888; 
                letter-spacing: 4px; 
                text-transform: uppercase; 
                text-align: center; 
                margin-bottom: 40px; 
            }

            .container { width: 100%; max-width: 700px; }

            .card { 
                background-color: #1e1e1e; 
                border-radius: 12px; 
                padding: 30px; 
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
                border: 1px solid #333;
            }

            /* Inputs & Search */
            .search-bar { display: flex; gap: 15px; margin-bottom: 10px; }
            input[type="text"] { 
                flex: 1; 
                padding: 16px; 
                border-radius: 8px; 
                border: 1px solid #333; 
                background-color: #121212; 
                color: #ffffff; 
                font-size: 18px; 
                font-weight: bold;
                outline: none;
                transition: border-color 0.2s;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            input[type="text"]:focus { border-color: #f39c12; }
            input[type="text"]::placeholder { color: #555; font-weight: normal; letter-spacing: normal; }

            .error-message { color: #ef4444; font-size: 14px; font-weight: bold; margin-bottom: 20px; display: none; text-align: center; }

            button { 
                padding: 16px 30px; 
                border: none; 
                border-radius: 8px; 
                font-weight: bold; 
                cursor: pointer; 
                transition: opacity 0.2s, transform 0.2s; 
                font-size: 16px; 
            }
            button:hover { opacity: 0.9; transform: translateY(-2px); }
            button:active { transform: translateY(0); }

            .btn-search { background-color: #f39c12; color: white; } 
            .btn-clear { background-color: transparent; border: 1px solid #444; color: #a0a0a0; width: 100%; margin-top: 15px; }
            .btn-action { background-color: #333333; color: white; padding: 8px 16px; font-size: 14px; border-radius: 6px; }

            .section-label { font-size: 11px; text-transform: uppercase; color: #888888; font-weight: bold; letter-spacing: 1px; margin-bottom: 12px; display: block; }

            /* Sleek Table Design */
            table { width: 100%; border-collapse: collapse; }
            th { text-align: left; padding: 16px 12px; border-bottom: 1px solid #333333; color: #888888; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
            td { padding: 16px 12px; border-bottom: 1px solid #2a2a2a; font-size: 15px; }
            tr:last-child td { border-bottom: none; }
            tr:hover td { background-color: #2a2a2a; }

            /* Result Card */
            .result-card { background-color: #121212; border: 1px solid #333; border-radius: 8px; padding: 25px; margin-top: 20px; display: none; text-align: center; }

            .spot-display { font-size: 3.5rem; font-weight: 800; letter-spacing: 4px; margin: 15px 0; }

            .details-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; text-align: left; background-color: #1a1a1a; padding: 20px; border-radius: 8px; border: 1px solid #222; }
            .detail-item { display: flex; flex-direction: column; gap: 5px; }
            .detail-item span.label { color: #888; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
            .detail-item span.value { font-weight: bold; color: #fff; font-size: 16px; }

            .bottom-link { color: #666; text-decoration: none; font-size: 14px; transition: color 0.2s; display: block; margin-top: 40px; text-align: center; }
            .bottom-link:hover { color: #ffffff; }

        </style>
    </head>
    <body>
        <div class="header-title">
            <h1 class="main-title">ParkSmart</h1>
            <span class="subtitle">Vehicle Directory</span>
        </div>

        <div class="container">
            <div class="card">
                <span class="section-label">Find a Parked Vehicle</span>
                <div class="search-bar">
                    <input type="text" id="searchInput" placeholder="ENTER PLATE OR SPOT ID..." autocomplete="off">
                    <button class="btn-search" onclick="executeSearch()">🔍 Locate</button>
                </div>

                <div id="searchError" class="error-message"></div>

                <!-- Result Card -->
                <div id="resultCard" class="result-card">
                    <span class="section-label" style="color: #00d09c;">Vehicle Located</span>

                    <div class="spot-display" id="resSpot"></div>

                    <div class="details-grid">
                        <div class="detail-item"><span class="label">License Plate</span><span class="value" id="resPlate"></span></div>
                        <div class="detail-item"><span class="label">Vehicle Type</span><span class="value" id="resType"></span></div>
                        <div class="detail-item"><span class="label">Time of Entry</span><span class="value" id="resEntry"></span></div>
                        <div class="detail-item"><span class="label">Time Parked</span><span class="value" id="resDuration"></span></div>
                        <div class="detail-item" style="grid-column: span 2; text-align: center; margin-top: 10px; padding-top: 15px; border-top: 1px solid #333;">
                            <span class="label">Current Accrued Fee</span>
                            <span class="value" id="resFee" style="color: #f39c12; font-size: 20px;"></span>
                        </div>
                    </div>

                    <button class="btn-clear" onclick="clearSearch()">Clear Search</button>
                </div>

                <!-- Live Table -->
                <div id="tableContainer">
                    <span class="section-label" style="margin-top: 15px;">Active Sessions Database</span>
                    <table>
                        <thead>
                            <tr>
                                <th>License Plate</th>
                                <th>Spot ID</th>
                                <th>Entry Time</th>
                                <th>Type</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody id="sessionsBody">
                            <!-- JS Populates Rows Here -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <a href="/operator/dashboard" class="bottom-link">&larr; Back to Dashboard</a>

        <script>
            // 1. Fetch data on load
            async function loadActiveSessions() {
                try {
                    const response = await fetch('/operator/api/active-sessions');
                    const data = await response.json();

                    if (data.status === 'success') {
                        const tbody = document.getElementById('sessionsBody');
                        tbody.innerHTML = ''; 

                        data.sessions.forEach(session => {
                            // Dynamic Spot ID Color Logic
                            let spotColor = '#3b82f6'; 
                            if (session.type === 'C') spotColor = '#22c55e';
                            else if (session.type === 'T') spotColor = '#f97316';

                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td style="font-weight: bold; text-transform: uppercase;">${session.plate}</td>
                                <td style="color: ${spotColor}; font-weight: bold; text-transform: uppercase;">${session.spot}</td>
                                <td style="color: #a0a0a0;">${session.entry}</td>
                                <td style="color: #a0a0a0;">${session.type}</td>
                                <td>
                                    <button class="btn-action" onclick="lookupFromTable('${session.plate}')">Select</button>
                                </td>
                            `;
                            tbody.appendChild(row);
                        });
                    }
                } catch (error) {
                    console.error("Failed to load sessions:", error);
                }
            }

            // 2. Live Typing Filter
            document.getElementById('searchInput').addEventListener('input', function(e) {
                const searchString = e.target.value.toUpperCase();
                const rows = document.querySelectorAll('#sessionsBody tr');

                rows.forEach(row => {
                    const plate = row.cells[0].textContent.toUpperCase();
                    const spot = row.cells[1].textContent.toUpperCase();

                    if (plate.includes(searchString) || spot.includes(searchString)) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            });

            // Trigger lookup from table Select button
            function lookupFromTable(query) {
                document.getElementById('searchInput').value = query.toUpperCase();
                executeSearch();
            }

            // Allow pressing "Enter" in the search box to trigger the search
            document.getElementById("searchInput").addEventListener("keypress", function(event) {
                if (event.key === "Enter") {
                    event.preventDefault();
                    executeSearch();
                }
            });

            async function executeSearch() {
                const query = document.getElementById('searchInput').value.trim();
                const errorDiv = document.getElementById('searchError');
                const resultCard = document.getElementById('resultCard');
                const tableContainer = document.getElementById('tableContainer');

                errorDiv.style.display = 'none'; 
                resultCard.style.display = 'none';

                if (!query) {
                    errorDiv.innerText = "Please enter a valid Plate or Spot ID.";
                    errorDiv.style.display = 'block';
                    return;
                }

                try {
                    const response = await fetch('/operator/api/search-vehicle', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ search_query: query })
                    });
                    const result = await response.json();

                    if (result.status === 'success') {
                        // Dynamic color coding for the large Spot ID text
                        const spotElement = document.getElementById('resSpot');
                        spotElement.innerText = result.spot;
                        if (result.type === 'C') spotElement.style.color = '#22c55e';
                        else if (result.type === 'T') spotElement.style.color = '#f97316';
                        else spotElement.style.color = '#3b82f6';

                        // Populate details
                        document.getElementById('resPlate').innerText = result.plate;
                        document.getElementById('resType').innerText = result.type === 'S' ? 'Two-Wheeler (S)' : result.type === 'C' ? 'Car (C)' : 'Heavy (T)';
                        document.getElementById('resEntry').innerText = result.entry;
                        document.getElementById('resDuration').innerText = result.duration;
                        document.getElementById('resFee').innerText = '₹' + result.fee;

                        // Hide table, show result
                        tableContainer.style.display = 'none';
                        resultCard.style.display = 'block';
                    } else {
                        errorDiv.innerText = result.message;
                        errorDiv.style.display = 'block';
                    }
                } catch (error) {
                    errorDiv.innerText = "Error connecting to the database.";
                    errorDiv.style.display = 'block';
                }
            }

            function clearSearch() {
                document.getElementById('searchInput').value = '';
                document.getElementById('resultCard').style.display = 'none';
                document.getElementById('searchError').style.display = 'none';
                document.getElementById('tableContainer').style.display = 'block'; // Unhide table

                // Reset table filter
                const rows = document.querySelectorAll('#sessionsBody tr');
                rows.forEach(row => row.style.display = '');

                document.getElementById('searchInput').focus();
            }

            // Load table data on startup
            document.addEventListener('DOMContentLoaded', loadActiveSessions);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ---------------------------------------------------------
# API ROUTE: Search for a Parked Vehicle
# ---------------------------------------------------------
@router.post("/operator/api/search-vehicle")
async def search_vehicle_api(data: VehicleExitSchema):
    try:
        result = OperatorTerminal.process_web_search(data.search_query)

        if result.get("status") == "success":
            return JSONResponse(content=result)
        else:
            return JSONResponse(status_code=404, content={"status": "error", "message": "Vehicle not found. It may not be parked here."})

    except Exception as e:
        print(f"Backend error during search: {str(e)}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Server error during search."})


# ---------------------------------------------------------
# API ROUTE: Fetch Live Parking Map Data
# ---------------------------------------------------------
@router.get("/operator/api/live-map")
async def get_live_map():
    try:
        parking_lot.cursor.execute("""
                                   SELECT m.floor_no, m.v_type, m.spot_no, m.spot_id, a.plate_no
                                   FROM lot_inventory m
                                            LEFT JOIN active_sessions a ON m.spot_id = a.spot_id
                                   ORDER BY m.floor_no ASC, m.v_type ASC, m.spot_no ASC
                                   """)

        all_spots = parking_lot.cursor.fetchall()

        floors = {}
        for floor, vtype, spot_no, spot_id, plate in all_spots:
            if floor not in floors:
                floors[floor] = []

            floors[floor].append({
                "spot_id": spot_id,
                "type": vtype,
                "plate": plate,
                "is_free": plate is None
            })

        return JSONResponse(content={"status": "success", "floors": floors})

    except Exception as e:
        print(f"Error fetching live map: {str(e)}")
        return JSONResponse(status_code=500, content={"status": "error"})