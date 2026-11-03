import asyncio
import aiohttp
import json
import sqlite3
import warnings

from src.api_clients.riot_api import calculate_player_form

# Filtrowanie ostrzeżeń o lokalnym certyfikacie SSL Riotu
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

LIVE_API_URL = "https://127.0.0.1:2999/liveclientdata/allgamedata"
DB_PATH = "knowledge_base.db"

class StateManager:
    """Odpowiada za śledzenie historii złota gracza w czasie."""
    def __init__(self):
        self.gold_history = []  # Lista krotek: (czas_w_sekundach, zebrane_zloto)

    def analyze_income(self, current_time: float, current_gold: int) -> str | None:
        self.gold_history.append((current_time, current_gold))
        
        if len(self.gold_history) < 3:
            return None

        t3, g3 = self.gold_history[-1]
        t2, g2 = self.gold_history[-2]
        t1, g1 = self.gold_history[-3]

        income_latest = g3 - g2
        income_previous = g2 - g1

        if income_previous > 0 and income_latest < (income_previous * 0.5):
            return f"⚠️ Twój przyrost złota drastycznie spadł ({income_latest}g vs {income_previous}g wcześniej). Skup się na farmieniu!"
        
        return None

class RuleEngine:
    """Odpowiada za logikę decyzyjną i odpytywanie bazy danych."""
    def __init__(self, db_path):
        self.db_path = db_path
        self.THREAT_THRESHOLD = 800

    def get_counter_item(self, player_class: str, enemy_name: str, enemy_gold_lead: int) -> str | None:
        if enemy_gold_lead < self.THREAT_THRESHOLD:
            return None

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT primary_damage FROM champions WHERE champ_name = ?", (enemy_name,))
            champ_result = cursor.fetchone()
            
            if not champ_result:
                return f"⚠️ {enemy_name} ma {enemy_gold_lead}g przewagi, ale brakuje go w bazie."
                
            enemy_damage_type = champ_result[0]

            cursor.execute("""
                SELECT item_name FROM defensive_items 
                WHERE target_class = ? AND (defends_against = ? OR defends_against = 'ALL')
                LIMIT 1
            """, (player_class, enemy_damage_type))
            
            item_result = cursor.fetchone()
            
            if item_result:
                return f"🛡️ ZAGROŻENIE: {enemy_name} ({enemy_damage_type} DMG) ma {enemy_gold_lead}g przewagi! Kup: {item_result[0]}."
            return None

def load_items_dict() -> dict:
    try:
        with open("data_cache/items.json", "r", encoding="utf-8") as f:
            return json.load(f)["data"]
    except FileNotFoundError:
        print("Błąd: Nie znaleziono data_cache/items.json!")
        return {}

def calculate_inventory_value(items_list: list, items_dict: dict) -> int:
    total_gold = 0
    for item in items_list:
        item_id = str(item["itemID"])
        if item_id in items_dict:
            total_gold += items_dict[item_id]["gold"]["total"]
    return total_gold

async def main_loop():
    items_dict = load_items_dict()
    if not items_dict:
        return

    state_manager = StateManager()
    rule_engine = RuleEngine(DB_PATH)
    
    MY_CLASS = "Bruiser"
    LOOP_INTERVAL = 10 
    
    # Sprawdzone nicki graczy, mniej zapytań do Riot API w trakcie meczu
    analyzed_players = set()
    
    connector = aiohttp.TCPConnector(ssl=False)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        print("Oczekiwanie na dołączenie do meczu...")
        
        while True:
            try:
                async with session.get(LIVE_API_URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        game_time = data["gameData"]["gameTime"]
                        active_player_name = data["activePlayer"]["summonerName"]
                        
                        print(f"\n--- ANALIZA: {game_time // 60:.0f}m {game_time % 60:.0f}s ---")
                        
                        player_gold = 0
                        enemies = []
                        
                        for player in data["allPlayers"]:
                            inventory_value = calculate_inventory_value(player.get("items", []), items_dict)
                            # Pobieranie RiodId lub summonerName
                            player_name = player.get("riotIdGameName") or player.get("summonerName", "Nieznany")
                            player_tag = player.get("riotIdTagline") or "EUW" # Domyślny tag, jeśli Live API go nie zwróci
                            
                            if player["summonerName"] == active_player_name:
                                player_gold = inventory_value
                            elif player["team"] != data["activePlayer"].get("team"):
                                enemies.append({
                                    "name": player_name, 
                                    "tag": player_tag,
                                    "champ_name": player["championName"], 
                                    "gold": inventory_value
                                })
                        
                        print(f"Twoje złoto w przedmiotach: {player_gold}g")
                        
                        # Analiza dochodów
                        income_advice = state_manager.analyze_income(game_time, player_gold)
                        if income_advice:
                            print(income_advice)
                            
                        # Przeciwnicy, analizujemy przedmkoty i ich formę
                        for enemy in enemies:
                            # 1. Sprawdzanie formy (Riot API)
                            full_id = f"{enemy['name']}#{enemy['tag']}"
                            if full_id not in analyzed_players:
                                print(f"Pobieranie historii meczów gracza: {full_id}...")
                                form = await calculate_player_form(session, enemy["name"], enemy["tag"])
                                
                                if not form.get("error"):
                                    if form["is_on_streak"]:
                                        print(f"🚨 ALERT FORMY: {full_id} ma winstreak! (Winrate: {form['winrate']}%, KDA: {form['kda']})")
                                    else:
                                        print(f"ℹ️ Forma {full_id}: {form['winrate']}% winrate, KDA: {form['kda']}")
                                else:
                                    # Wyświetla błąd, jeśli API Riotu odrzuci gracza
                                    print(f"❌ Błąd pobierania formy dla {full_id}: {form.get('message')}")
                                
                                analyzed_players.add(full_id)
                            
                            # 2. Sprawdzanie przewagi i dobór przedmiotów (SQLite)
                            gold_lead = enemy["gold"] - player_gold
                            advice = rule_engine.get_counter_item(MY_CLASS, enemy["champ_name"], gold_lead)
                            if advice:
                                print(advice)
                                
                    else:
                        print("Mecz nieaktywny, czekam...")
                        
            except aiohttp.ClientConnectorError:
                print("Gra wyłączona. Uruchom mecz, aby kontynuować.")
            
            await asyncio.sleep(LOOP_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main_loop())