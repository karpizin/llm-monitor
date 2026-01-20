import requests
import json
import logging
from database import save_models

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_discovery():
    logger.info("Starting model discovery...")
    url = "https://openrouter.ai/api/v1/models"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        models = data.get("data", [])
        processed_models = []
        
        for model in models:
            pricing = model.get("pricing", {})
            # Check free pricing
            is_free_price = pricing.get("prompt") == "0" and pricing.get("completion") == "0"
            is_free_id = model.get("id", "").endswith(":free")
            
            if is_free_price or is_free_id:
                arch = model.get("architecture", {})
                input_mods = arch.get("input_modalities", [])
                
                # Check VLM
                is_vlm = "image" in input_mods or "image" in arch.get("modality", "")
                
                processed_models.append({
                    "id": model.get("id"),
                    "name": model.get("name"),
                    "context": model.get("context_length", 0),
                    "is_vlm": is_vlm
                })
        
        if processed_models:
            save_models(processed_models)
            logger.info(f"Discovery complete. Found and saved {len(processed_models)} free models.")
        else:
            logger.warning("Discovery found 0 models. Check API response.")
            
    except Exception as e:
        logger.error(f"Error during discovery: {e}")

if __name__ == "__main__":
    run_discovery()