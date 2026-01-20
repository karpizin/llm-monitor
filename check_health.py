import sqlite3
import os
import time
import requests
import logging
from database import get_connection, add_notification

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def run_health_check():
    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not set. Skipping health checks.")
        return

    logger.info("Starting health checks...")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get active models
    cursor.execute("SELECT id FROM models WHERE is_active = 1")
    models = [row[0] for row in cursor.fetchall()]
    
    for model_id in models:
        check_model(model_id, cursor)
        
    conn.commit()
    conn.close()
    logger.info("Health checks completed.")

def check_model(model_id, cursor):
    # 1. Get previous state
    cursor.execute("SELECT success FROM checks WHERE model_id = ? ORDER BY timestamp DESC LIMIT 1", (model_id,))
    row = cursor.fetchone()
    prev_success = row[0] if row else None

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/karpizin/llm-monitor",
        "X-Title": "LLM Monitor"
    }
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 1
    }
    
    start_time = time.time()
    success = False
    error_msg = None
    status_code = 0
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        status_code = response.status_code
        latency_ms = int((time.time() - start_time) * 1000)
        
        if status_code == 200:
            success = True
        else:
            error_msg = f"HTTP {status_code}: {response.text[:100]}"
            
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        error_msg = str(e)
        
    # Save result
    cursor.execute("""
        INSERT INTO checks (model_id, status_code, latency_ms, success, error_msg)
        VALUES (?, ?, ?, ?, ?)
    """, (model_id, status_code, latency_ms, success, error_msg))
    
    # Detect state change
    if prev_success is not None and prev_success != success:
        if success:
            msg = f"🟢 Model restored: {model_id}"
        else:
            msg = f"🔴 Model down: {model_id} ({error_msg})"
        add_notification(msg)
        logger.info(f"Notification queued: {msg}")
    
    if success:
        logger.info(f"✅ {model_id}: {latency_ms}ms")
    else:
        logger.warning(f"❌ {model_id}: {error_msg}")

if __name__ == "__main__":
    run_health_check()
