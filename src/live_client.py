import asyncio
import aiohttp
import warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

LIVE_API_URL = "https://127.0.0.1:2999/liveclientdata/allgamedata"

async def fetch_live_match_state():
    # Próbna zmiana, ssl=False zamiast przestarzałego(depreciated) verify_ssl=False
    connector = aiohttp.TCPConnector(ssl=False)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            print("Próba połączenia z Live Client API...")
            async with session.get(LIVE_API_URL) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    game_time = data["gameData"]["gameTime"]
                    active_player_name = data["activePlayer"]["summonerName"]
                    
                    print("\n--- POŁĄCZONO Z GRĄ ---")
                    print(f"Gracz: {active_player_name}")
                    print(f"Czas gry: {game_time // 60:.0f} min {game_time % 60:.0f} s")
                    
                    # Próbna zmiana: szukanie ekwipunku w tablicy allPlayers a nie w activePlayer
                    active_player_items = []
                    for player in data["allPlayers"]:
                        if player["summonerName"] == active_player_name:
                            active_player_items = player.get("items", [])
                            break
                            
                    print(f"Masz aktualnie przedmiotów: {len(active_player_items)}")
                    
                    # TO DO Robocze wypisywanie nazw przedmiotow to sprawdzania 
                    for item in active_player_items:
                        print(f"- {item['displayName']} (ID: {item['itemID']})")
                    
                    return data
                
                elif response.status == 404:
                    print("Błąd 404: Jesteś w lobby, a nie w trakcie meczu.")
                else:
                    print(f"Nieoczekiwany błąd HTTP: {response.status}")
                    
        except aiohttp.ClientConnectorError:
            print("Błąd połączenia. Upewnij się, że gra jest uruchomiona.")

if __name__ == "__main__":
    asyncio.run(fetch_live_match_state())