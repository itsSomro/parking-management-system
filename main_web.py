from fastapi import FastAPI
import uvicorn

from routers import admin, auth, operator

app = FastAPI()

app.include_router(auth.router)
app.include_router(admin.router)

# app.include_router(operator.router)

if __name__ == "__main__":
    uvicorn.run("main_web:app", host="127.0.0.1", port=8000, reload=True)