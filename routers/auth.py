from fastapi import APIRouter, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from db.Database import Database


router = APIRouter()
db = Database()


# ---------------------------------------------------------------------------------------
# 1. VISUAL LOGIN PAGE (GET)
# ---------------------------------------------------------------------------------------
@router.get("/login", response_class=HTMLResponse)
def show_login_page():
    html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Login - ParkSmart</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&display=swap');

                body { background-color: #121212; color: white; font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .login-box { background-color: #1e1e1e; padding: 50px 40px; border-radius: 12px; border: 1px solid #333; width: 100%; max-width: 420px; box-sizing: border-box; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }

                h1.main-title { text-align: center; font-family: 'Cinzel', serif; font-weight: 800; font-size: 3.2rem; margin-top: 0; margin-bottom: 5px; color: #ffffff; letter-spacing: 3px; }
                .subtitle { display: block; font-family: sans-serif; font-size: 1rem; color: #888; letter-spacing: 4px; text-transform: uppercase; text-align: center; margin-bottom: 40px; }

                .input-group { margin-bottom: 25px; }
                .input-group label { display: block; margin-bottom: 8px; color: #aaaaaa; font-size: 0.95rem; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }
                .input-group input { width: 100%; padding: 15px; border-radius: 8px; border: 1px solid #444; background-color: #2a2a2a; color: white; font-size: 1.1rem; box-sizing: border-box; transition: border-color 0.2s; }
                .input-group input:focus { outline: none; border-color: #00d09c; }

                .submit-btn { width: 100%; padding: 16px; background-color: #00d09c; color: #121212; border: none; border-radius: 8px; font-size: 1.2rem; font-weight: bold; cursor: pointer; transition: background-color 0.2s; margin-top: 10px; }
                .submit-btn:hover { background-color: #00a87d; }
            </style>
        </head>
        <body>
            <div class="login-box">
                <h1 class="main-title">ParkSmart</h1>
                <span class="subtitle">System Login</span>

                <form action="/login" method="POST">
                    <div class="input-group">
                        <label for="username">Username</label>
                        <input type="text" id="username" name="username" required autocomplete="off">
                    </div>
                    <div class="input-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit" class="submit-btn">Sign In</button>
                </form>
            </div>
        </body>
        </html>
        """
    return HTMLResponse(content=html_content)


# ---------------------------------------------------------------------------------------
# 2. LOGIN VERIFICATION LOGIC (POST)
# ---------------------------------------------------------------------------------------
@router.post("/login")
def handle_login(
        response: Response,
        username: str = Form(...),
        password: str = Form(...)
):
    verification, role = db.verify_login(username, password)

    if verification:
        if role.lower() == 'admin':
            redirect_url = "/admin/dashboard"
        else:
            redirect_url = "/operator/dashboard"

        redirect = RedirectResponse(url=redirect_url, status_code=302)
        redirect.set_cookie(key="access_token", value=f"{username}_{role}")
        return redirect
    else:
        return HTMLResponse(
            content="<h2 style='color: white; background-color: #121212; height: 100vh; text-align: center; padding-top: 50px;'>[!] Access Denied: Invalid Username or Password. <br><br> <a href='/login' style='color: #00d09c;'>Try Again</a></h2>")


# ---------------------------------------------------------------------------------------
# 3. LOGOUT LOGIC (GET)
# ---------------------------------------------------------------------------------------
@router.get("/logout")
def logout_user():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response