import urllib.request
import json

def fetch_free_models():
    url = "https://openrouter.ai/api/v1/models"
    try:
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                print(f"Error: Server returned status {response.status}")
                return []
            data = json.loads(response.read().decode('utf-8'))
        
        models = data.get("data", [])
        processed_models = []
        
        for model in models:
            pricing = model.get("pricing", {})
            is_free = pricing.get("prompt") == "0" and pricing.get("completion") == "0"
            is_free_id = model.get("id", "").endswith(":free")
            
            if is_free or is_free_id:
                arch = model.get("architecture", {})
                input_mods = arch.get("input_modalities", [])
                
                # Check if it's a VLM
                is_vlm = "image" in input_mods or "image" in arch.get("modality", "")
                
                processed_models.append({
                    "id": model.get("id"),
                    "name": model.get("name"),
                    "context": model.get("context_length", 0),
                    "is_vlm": is_vlm
                })
        
        return processed_models

    except Exception as e:
        print(f"Error fetching models: {e}")
        return []

if __name__ == "__main__":
    print("Fetching filtered free models from OpenRouter...")
    all_free = fetch_free_models()
    
    # 1. High Context (>= 60,000)
    high_context = [m for m in all_free if m['context'] >= 60000]
    
    # 2. Vision Models (VLM)
    vlm_models = [m for m in all_free if m['is_vlm']]

    print(f"\n--- HIGH CONTEXT FREE MODELS (>= 60k) [{len(high_context)}] ---")
    print(f"{'ID':<60} | {'Context':<10}")
    print("-" * 75)
    for m in sorted(high_context, key=lambda x: x['context'], reverse=True):
        print(f"{m['id']:<60} | {m['context']:<10}")

    print(f"\n--- VISION FREE MODELS (VLM) [{len(vlm_models)}] ---")
    print(f"{'ID':<60} | {'Context':<10}")
    print("-" * 75)
    for m in sorted(vlm_models, key=lambda x: x['id']):
        print(f"{m['id']:<60} | {m['context']:<10}")
