import os
import asyncio
import aiohttp
import urllib.parse
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
REGION_ROUTING = "europe"

if not API_KEY:
    raise ValueError("Brak RIOT_API_KEY w pliku .env!")

HEADERS = {"X-Riot-Token": API_KEY}

async def get_puuid(session: aiohttp.ClientSession, game_name: str, tag_line: str) -> str:
    safe_name = urllib.parse.quote(game_name)
    safe_tag = urllib.parse.quote(tag_line)
    url = f"https://{REGION_ROUTING}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{safe_name}/{safe_tag}"
    
    async with session.get(url, headers=HEADERS) as response:
        response.raise_for_status()
        data = await response.json()
        return data["puuid"]

async def get_last_5_matches(session: aiohttp.ClientSession, puuid: str) -> list[str]:
    url = f"https://{REGION_ROUTING}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count=5"
    
    async with session.get(url, headers=HEADERS) as response:
        response.raise_for_status()
        return await response.json()

async def parse_match_stats(session: aiohttp.ClientSession, match_id: str, puuid: str) -> dict | None:
    url = f"https://{REGION_ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    
    async with session.get(url, headers=HEADERS) as response:
        response.raise_for_status()
        data = await response.json()

    info = data["info"]
    participant = next((p for p in info["participants"] if p["puuid"] == puuid), None)
    
    if not participant:
        return None

    return {
        "win": participant["win"],
        "kills": participant["kills"],
        "deaths": participant["deaths"],
        "assists": participant["assists"]
    }

async def calculate_player_form(session: aiohttp.ClientSession, game_name: str, tag_line: str) -> dict:
    """Pobiera dane gracza i oblicza wskaźnik formy na podstawie 5 ostatnich meczów."""
    try:
        puuid = await get_puuid(session, game_name, tag_line)
        match_ids = await get_last_5_matches(session, puuid)
        
        # Zrównoleglenie pobierania szczegółów meczów
        tasks = [parse_match_stats(session, match_id, puuid) for match_id in match_ids]
        results = await asyncio.gather(*tasks)
        
        # Filtrowanie pustych wyników
        valid_matches = [res for res in results if res is not None]
        
        if not valid_matches:
            return {"error": True, "message": "Brak danych o meczach."}
            
        wins = sum(1 for m in valid_matches if m["win"])
        winrate = (wins / len(valid_matches)) * 100
        total_kills = sum(m["kills"] for m in valid_matches)
        total_deaths = sum(m["deaths"] for m in valid_matches)
        total_assists = sum(m["assists"] for m in valid_matches)
        
        kda = (total_kills + total_assists) / max(1, total_deaths)
        
        return {
            "error": False,
            "game_name": game_name,
            "wins": wins,
            "total_matches": len(valid_matches),
            "winrate": winrate,
            "kda": round(kda, 2),
            "is_on_streak": wins >= 4  # Flaga ostrzegawcza (wygrał 4+ z 5 meczów)
        }
        
    except aiohttp.ClientResponseError as e:
        return {"error": True, "message": f"Błąd API: {e.status}"}
    except Exception as e:
        return {"error": True, "message": str(e)}

# Szybki test działania modułu
if __name__ == "__main__":
    async def test_module():
        async with aiohttp.ClientSession() as session:
            form = await calculate_player_form(session, "Faker", "KR1")
            print(form)
            
    asyncio.run(test_module())