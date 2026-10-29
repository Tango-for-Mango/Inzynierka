import os
import asyncio
import aiohttp
import urllib.parse
from dotenv import load_dotenv

# 1. Wczytanie konfiguracji z .env
load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
REGION_ROUTING = "europe"

if not API_KEY:
    raise ValueError("Brak RIOT_API_KEY w pliku .env! Upewnij się, że plik istnieje.")

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


async def parse_match(session: aiohttp.ClientSession, match_id: str, puuid: str):
    url = f"https://{REGION_ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    
    async with session.get(url, headers=HEADERS) as response:
        response.raise_for_status()
        data = await response.json()

    info = data["info"]
    game_mode = info.get("gameMode", "CLASSIC")
    participant = next((p for p in info["participants"] if p["puuid"] == puuid), None)
    
    if not participant:
        return

    win = " Wygrana " if participant["win"] else "Przegrana"
    print(f"[{win}] Tryb Gry: {game_mode:<8} | Czempion: {participant['championName']:<12} | KDA: {participant['kills']}/{participant['deaths']}/{participant['assists']}")


async def main():
    raw_input = input("Wpisz RIOT ID (np. Faker#KR1): ").strip()
    # Usuwanie spacji dla komfortu
    if "#" not in raw_input:
        print("Błąd: Dodaj swój tag (np. TwójNick#EUW).")
        return

    game_name, tag_line = raw_input.split("#", 1)
    print(f"\nSprawdzanie {game_name}#{tag_line}...")

    # Utworzenie jednej sesji dla zapytań
    async with aiohttp.ClientSession() as session:
        try:
            puuid = await get_puuid(session, game_name, tag_line)
            match_ids = await get_last_5_matches(session, puuid)
            
            print(f"Znaleziono {len(match_ids)} meczy. Sprawdzanie szczegółów...\n")
            
            # Zrównoleglenie zapytań o szczegóły meczów
            tasks = [parse_match(session, match_id, puuid) for match_id in match_ids]
            await asyncio.gather(*tasks)
            
        except aiohttp.ClientResponseError as e:
            print(f"Błąd zwrotu od API. Błąd: {e.status} - {e.message}")


if __name__ == "__main__":
    asyncio.run(main())