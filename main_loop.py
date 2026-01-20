import schedule
import time
import logging
import os
from discovery_free import run_discovery
from check_health import run_health_check
from database import init_db

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("main-loop")

def main():
    logger.info("Initializing LLM Monitor...")
    
    # 1. Init Database
    init_db()
    
    # 2. Run initial discovery
    run_discovery()
    
    # 3. Schedule tasks
    # Discovery every hour
    schedule.every(1).hours.do(run_discovery)
    
    # Health check every 10 minutes
    schedule.every(10).minutes.do(run_health_check)
    
    logger.info("Scheduler started. Running loop...")
    
    # Initial health check
    run_health_check()
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
