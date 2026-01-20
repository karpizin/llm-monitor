import os
import sqlite3
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from database import get_connection

app = FastAPI(title="LLM Monitor Dashboard")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Fetch latest status for each model
    query = """
        SELECT m.id, m.is_vlm, c.success, c.latency_ms, c.timestamp
        FROM models m
        LEFT JOIN checks c ON c.id = (
            SELECT id FROM checks WHERE model_id = m.id ORDER BY timestamp DESC LIMIT 1
        )
        WHERE m.is_active = 1
        ORDER BY c.success DESC, c.latency_ms ASC
    """
    cursor.execute(query)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return templates.TemplateResponse("index.html", {"request": request, "models": rows})

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
