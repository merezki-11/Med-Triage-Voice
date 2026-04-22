import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.routers import triage

app = FastAPI(title="Med-Triage Voice API", version="1.0.0")

# Mount static files
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(triage.router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("app/static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Frontend not found</h1><p>Please ensure app/static/index.html exists.</p>", status_code=404)
