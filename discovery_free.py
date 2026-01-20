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
        free_models = []
        
        for model in models:
            pricing = model.get("pricing", {})
            # Check if both prompt and completion are free ("0")
            # OpenRouter often provides pricing as strings
            is_free_price = pricing.get("prompt") == "0" and pricing.get("completion") == "0"
            
            # Also check ID suffix as a backup/alternative indicator
            is_free_id = model.get("id", "").endswith(":free")
            
            if is_free_price or is_free_id:
                free_models.append({
                    "id": model.get("id"),
                    "name": model.get("name"),
                    "context": model.get("context_length")
                })
        
        return free_models

    except Exception as e:
        print(f"Error fetching models: {e}")
        return []

if __name__ == "__main__":
    print("Fetching free models from OpenRouter using urllib...")
    free_list = fetch_free_models()
    
    print(f"\nFound {len(free_list)} free models:\n")
    print(f"{'ID':<60} | {'Context':<10}")
    print("-" * 75)
    
    # Sort and print
    for m in sorted(free_list, key=lambda x: x['id']):
        print(f"{m['id']:<60} | {m['context']:<10}")