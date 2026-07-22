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
    <html>
        <head>
            <title>System Login</title>
            <style>
                body {
                    background-color: #121212;
                    color: white;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .login-box {
                    background-color: #1e1e1e;
                    padding: 40px;
                    border-radius: 12px;
                    border: 1px solid #333;
                    width: 100%;
                    max-width: 400px;
                    box-sizing: border-box;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.5);
                }
                h2 { text-align: center; margin-top: 0; margin-bottom: 30px; color: #ffffff; }

                .input-group { margin-bottom: 20px; }
                .input-group label { display: block; margin-bottom: 8px; color: #aaaaaa; font-size: 0.9rem; }

                .input-group input {
                    width: 100%;
                    padding: 12px;
                    border-radius: 8px;
                    border: 1px solid #444;
                    background-color: #2a2a2a;
                    color: white;
                    font-size: 1rem;
                    box-sizing: border-box;
                    transition: border-color 0.2s;
                }
                .input-group input:focus { outline: none; border-color: #00d09c; }

                .submit-btn {
                    width: 100%;
                    padding: 15px;
                    background-color: #00d09c;
                    color: #121212;
                    border: none;
                    border-radius: 8px;
                    font-size: 1.1rem;
                    font-weight: bold;
                    cursor: pointer;
                    transition: background-color 0.2s;
                    margin-top: 10px;
                }
                .submit-btn:hover { background-color: #00a87d; }
            </style>
        </head>
        <body>
            <div class="login-box">
                <h2>Parking Control System</h2>

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
            redirect_url = "/operator"

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