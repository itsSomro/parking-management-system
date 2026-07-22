from fastapi import FastAPI, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
import plotly.graph_objects as go
import pandas as pd

from core.ParkingLot import ParkingLot
from db.Database import Database

app = FastAPI()
db = Database()
parking_lot = ParkingLot(db)

@app.post("/login")
def handle_login(
        response: Response,
        username: str = Form(...),
        password: str = Form(...)
):
    verification, role = db.verify_login(username, password)

    if verification:
        redirect = RedirectResponse(url="/admin/dashboard", status_code=302)
        redirect.set_cookie(key="access_token", value=f"{username}_{role}")
        return redirect
    else:
        return "<h2>[!] Access Denied: Invalid Username or Password.</h2>"



