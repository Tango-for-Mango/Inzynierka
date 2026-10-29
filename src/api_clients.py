import aiohttp
import asyncio
import json
import os

CACHE_DIR = "data_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

async def update_data_dragon():
    print("Sprawdzanie aktualnych plików Data Dragon...")
    
    async with aiohttp.ClientSession() as session:
        # Pobranie najnowszej wersji gry
        async with session.get("https://ddragon.leagueoflegends.com/api/versions.json") as resp:
            versions = await resp.json()
            latest_version = versions[0]
            
        # Pobranie słownika przedmiotów po polsku
        items_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/pl_PL/item.json"
        async with session.get(items_url) as resp:
            items_data = await resp.json()
            with open(f"{CACHE_DIR}/items.json", "w", encoding="utf-8") as f:
                json.dump(items_data, f, ensure_ascii=False, indent=4)
            print(f"Zapisano dane dla patcha {latest_version}.")

def get_item_stats(item_id: int) -> dict:
    #Zwraca koszt w złocie i tagi dla danego ID przedmiotu
    try:
        with open(f"{CACHE_DIR}/items.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            item_info = data["data"][str(item_id)]
            return {
                "name": item_info["name"],
                "gold_total": item_info["gold"]["total"],
                "tags": item_info.get("tags", [])
            }
    except (FileNotFoundError, KeyError):
        return {"name": "Nieznany", "gold_total": 0, "tags": []}

if __name__ == "__main__":
    # Jednorazowa aktualizacja
    asyncio.run(update_data_dragon())

    # Test 
    item_id = [3142, 6699, 3340, 3036, 3814]
    for curr in item_id:
        stats = get_item_stats(curr)
        print(f"\nStatystyki dla ID {curr}:")
        print(f"Nazwa: {stats['name']} | Koszt całkowity: {stats['gold_total']} golda | Tagi: {', '.join(stats['tags'])}")
