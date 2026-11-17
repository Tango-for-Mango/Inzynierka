import asyncio
import aiohttp
import json
import sqlite3
import warnings
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import urllib.parse
import traceback
import os
from dotenv import load_dotenv

load_dotenv()
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
print(f"Wczytany klucz: {RIOT_API_KEY}")

from src.api_clients.riot_api import calculate_player_form

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

LIVE_API_URL = "https://127.0.0.1:2999/liveclientdata/allgamedata"
DB_PATH = "knowledge_base.db"

# --- GLOBALNY STAN GRY (wysyłany do przeglądarki) ---
current_game_state = {
    "status": "Oczekiwanie na dołączenie do meczu...",
    "player_gold": 0,
    "threats": [],
    "income_advice": None
}

app_settings = {
    "riot_name": None,
    "riot_tag": None,
    "region": "eun1",
    "is_configured": False
}

class UserSettings(BaseModel):
    riot_name: str
    riot_tag: str
    region: str

class StateManager:
    def __init__(self):
        self.gold_history = []

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
            return f"⚠️ Twój przyrost złota drastycznie spadł. Skup się na farmieniu!"
        return None

class RuleEngine:
    def __init__(self, db_path):
        self.db_path = db_path
        self.THREAT_THRESHOLD = 800

    def get_counter_item(self, player_class: str, enemy_name: str, enemy_gold_lead: int) -> str | None:
        if enemy_gold_lead < self.THREAT_THRESHOLD:
            return None
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Pobieramy dokładne kolumny z Twojej tabeli champions
            cursor.execute("""
                SELECT primary_damage, high_healing, high_shielding, high_crit 
                FROM champions WHERE champ_name = ?
            """, (enemy_name,))
            champ_result = cursor.fetchone()
            
            if not champ_result:
                return f"⚠️ {enemy_name} ma {enemy_gold_lead}g przewagi, ale brakuje go w bazie."
                
            enemy_damage_type = champ_result[0]
            enemy_high_healing = bool(champ_result[1])
            enemy_high_shielding = bool(champ_result[2])
            enemy_high_crit = bool(champ_result[3])
            
            # 2. Pobieramy przedmioty i ich flagi z tabeli defensive_items
            cursor.execute("""
                SELECT item_name, is_anti_heal, is_anti_shield, is_anti_crit 
                FROM defensive_items 
                WHERE target_class = ? AND (defends_against = ? OR defends_against = 'ALL')
            """, (player_class, enemy_damage_type))
            
            items = cursor.fetchall()
            
            if items:
                final_items = []
                for item in items:
                    item_name = item[0]
                    is_anti_heal = bool(item[1])
                    is_anti_shield = bool(item[2])
                    is_anti_crit = bool(item[3])
                    
                    # 3. Genialnie proste filtrowanie - usuwamy przedmiot, jeśli leczy/tarczuje, 
                    # a przeciwnik nie ma takiej mechaniki
                    if is_anti_heal and not enemy_high_healing:
                        continue
                    if is_anti_shield and not enemy_high_shielding:
                        continue
                    if is_anti_crit and not enemy_high_crit:
                        continue
                        
                    final_items.append(item_name)

                if not final_items:
                    return None
                    
                items_str = ", ".join(final_items)
                return f"🛡️ ZAGROŻENIE: {enemy_name} ({enemy_damage_type} DMG) ma {enemy_gold_lead}g przewagi! Rozważ: {items_str}."
                
            return None

def load_items_dict() -> dict:
    try:
        with open("data_cache/items.json", "r", encoding="utf-8") as f:
            return json.load(f)["data"]
    except FileNotFoundError:
        print("Błąd: Nie znaleziono data_cache/items.json!")
        return {}

def calculate_inventory_value(items_data, items_dict: dict) -> int:
    # Zabezpieczenie przed brakiem danych lub pustą listą/słownikiem
    if not items_data: 
        return 0
    
    # Jeśli zbugowane API Riotu zwróci słownik zamiast listy
    if isinstance(items_data, dict):
        items_data = items_data.values()
    elif not isinstance(items_data, list):
        return 0
        
    total = 0
    for item in items_data:
        # Upewniamy się, że item jest faktycznie przedmiotem (słownikiem z ID)
        if isinstance(item, dict) and "itemID" in item:
            total += items_dict.get(str(item["itemID"]), {}).get("gold", {}).get("total", 0)
    return total

async def fetch_real_tags_from_spectator(session, my_name, my_tag, region, api_key):
    """Pobiera prawdziwe tagi Riot ID dla wszystkich graczy w obecnym meczu."""
    headers = {"X-Riot-Token": api_key}
    
    # NOWE: Bezpieczne kodowanie nicków ze spacjami (np. "Izraelski Shrek" -> "Izraelski%20Shrek")
    safe_name = urllib.parse.quote(my_name)
    safe_tag = urllib.parse.quote(my_tag)
    
    # 1. Pobranie Twojego PUUID
    account_url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{safe_name}/{safe_tag}"
    async with session.get(account_url, headers=headers) as resp:
        if resp.status != 200:
            print(f"Błąd konta: {resp.status}")
            return {}
        account_data = await resp.json()
        puuid = account_data["puuid"]

    # 2. Pobranie danych obecnego meczu
    spectator_url = f"https://{region}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{puuid}"
    async with session.get(spectator_url, headers=headers) as resp:
        if resp.status != 200:
            print(f"Błąd Spectator API: {resp.status} (w grach Custom/Treningowych to normalne)")
            return {}
        game_data = await resp.json()

    # 3. Zbudowanie słownika
    tags_map = {}
    for p in game_data.get("participants", []):
        riot_id = p.get("riotId", "")
        if "#" in riot_id:
            name, tag = riot_id.split("#", 1)
            tags_map[name] = tag
            
    return tags_map

def get_my_class(db_path, champ_name):
    """Pobiera klasę aktywnego gracza z bazy danych. Domyślnie Bruiser."""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            # Zakładamy, że w przyszłości dodasz kolumnę champ_class do tabeli champions
            cursor.execute("SELECT champ_class FROM champions WHERE champ_name = ?", (champ_name,))
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
    except sqlite3.OperationalError:
        pass # Ignorujemy błąd, jeśli kolumna champ_class jeszcze nie istnieje
    
    return "Bruiser"

# --- PĘTLA ANALIZUJĄCA GRĘ ---
async def game_analysis_loop():
    items_dict = load_items_dict()
    if not items_dict: return
    state_manager = StateManager()
    rule_engine = RuleEngine(DB_PATH)
    LOOP_INTERVAL = 10 
    analyzed_players = {}
    spectator_api_checked = False
    
    connector = aiohttp.TCPConnector(ssl=False)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        print("Uruchomiono analizator w tle. Nasłuchiwanie...")
        while True:
            # Blokada dopóki nie ma konfiguracji
            if not app_settings.get("is_configured"):
                current_game_state["status"] = "Wprowadź swoje dane i klucz API w panelu..."
                await asyncio.sleep(2)
                continue

            try:
                async with session.get(LIVE_API_URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        game_time = data["gameData"]["gameTime"]
                        
                        # LEPSZA IDENTYFIKACJA GRACZA I KLASY
                        active_player = data["activePlayer"]
                        active_player_name = active_player.get("riotIdGameName") or active_player.get("summonerName")
                        my_champion = active_player.get("championName")
                        
                        # Dynamiczne pobranie klasy gracza
                        MY_CLASS = get_my_class(DB_PATH, my_champion)
                        
                        current_game_state["status"] = f"Mecz w toku ({game_time // 60:.0f}m {game_time % 60:.0f}s)"
                        
                        if not spectator_api_checked:
                            spectator_api_checked = True
                            print("Pobieranie prawdziwych tagów ze Spectator API...")
                            try:
                                real_tags_cache = await fetch_real_tags_from_spectator(
                                    session, 
                                    app_settings["riot_name"], 
                                    app_settings["riot_tag"], 
                                    app_settings["region"],
                                    RIOT_API_KEY
                                )
                                if real_tags_cache:
                                    print(f"Sukces! Zmapowano tagi dla {len(real_tags_cache)} graczy.")
                                else:
                                    print("API nie zwróciło tagów. Używam tagów awaryjnych z gry.")
                            except Exception as e:
                                print(f"Błąd API Riotu (zignorowano): {e}")
                                real_tags_cache = {} # Zabezpieczenie przed błędem typu NoneType

                        player_gold = 0
                        enemies = []
                        new_threats = []
                        
                        for player in data["allPlayers"]:
                            # Bezpieczne pobieranie przedmiotów
                            items_list = player.get("items") or []
                            inventory_value = calculate_inventory_value(items_list, items_dict)
                            
                            player_name = player.get("riotIdGameName") or player.get("summonerName")
                            
                            # 1. Ignorowanie kukieł treningowych (puste sloty bez nazwy)
                            if not player_name:
                                continue  
                                
                            is_bot = player.get("isBot", False)
                            
                            # 2. Szukanie tagu tylko dla prawdziwych graczy, rozpoznawanie botów
                            if not is_bot:
                                player_tag = real_tags_cache.get(player_name) if real_tags_cache else None
                                
                                if not player_tag:
                                    player_tag = player.get("riotIdTagline")
                                    
                                if not player_tag or player_tag.strip() == "":
                                    custom_game_tags = {
                                        "Izraelski Shrek": "Swamp"
                                    }
                                    player_tag = custom_game_tags.get(player_name)
                            else:
                                player_tag = "BOT"
                                
                            # 3. Zabezpieczenie, żeby NIGDY nie wyrzucać gracza z analizy przedmiotów
                            if not player_tag:
                                player_tag = "BrakTagu"
                            
                            # PRZYPISYWANIE ZŁOTA
                            if player_name == active_player_name or player.get("summonerName") == active_player.get("summonerName"):
                                player_gold = inventory_value
                            elif player.get("team") != active_player.get("team"):
                                enemies.append({
                                    "name": player_name, 
                                    "tag": player_tag, 
                                    "champ_name": player["championName"], 
                                    "gold": inventory_value
                                })
                        
                        current_game_state["player_gold"] = player_gold
                        
                        income_advice = state_manager.analyze_income(game_time, player_gold)
                        if income_advice: new_threats.append(income_advice)
                            
                        for enemy in enemies:
                            full_id = f"{enemy['name']}#{enemy['tag']}"
                            
                            if full_id not in analyzed_players:
                                print(f"Sprawdzanie formy: {full_id}...")
                                form = await calculate_player_form(session, enemy["name"], enemy["tag"])
                                
                                if not form.get("error"):
                                    kda_str = form.get('kda', 'Brak danych')
                                    winrate = form.get('winrate', 0)
                                    
                                    if form.get("is_on_streak"):
                                        analyzed_players[full_id] = f"🚨 ZAGROŻENIE: {full_id} ma winstreak! (Winrate: {winrate}%, KDA: {kda_str})"
                                    else:
                                        # Pokazuje formę zawsze, nawet jeśli gracz nie ma winstreaka
                                        analyzed_players[full_id] = f"📊 Forma: {full_id} (Winrate: {winrate}%, KDA: {kda_str})"
                                else:
                                    # Przydatne w grach niestandardowych (gdy API Riotu zwraca błąd o botach)
                                    analyzed_players[full_id] = f"⚠️ {full_id}: Brak danych o meczach."
                            
                            if analyzed_players[full_id]:
                                new_threats.append(analyzed_players[full_id])
                            
                            gold_lead = enemy["gold"] - player_gold
                            advice = rule_engine.get_counter_item(MY_CLASS, enemy["champ_name"], gold_lead)
                            if advice: 
                                new_threats.append(advice)
                        
                        if not new_threats:
                            current_game_state["threats"] = ["Brak wykrytych zagrożeń. Farmij spokojnie!"]
                        else:
                            current_game_state["threats"] = new_threats
                            
                    else:
                        current_game_state["status"] = "Mecz nieaktywny, czekam..."
                        
            except aiohttp.ClientConnectorError:
                current_game_state["status"] = "Gra wyłączona. Uruchom mecz, aby kontynuować."
            except Exception as e:
                # Wypisze w konsoli dokładną ścieżkę i numer linijki z błędem
                print(f"\n--- BŁĄD KRYTYCZNY W PĘTLI ---")
                traceback.print_exc()
                print("------------------------------\n")
            
            await asyncio.sleep(LOOP_INTERVAL)

# --- KONFIGURACJA SERWERA FASTAPI ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Odpalamy pętlę gry jako zadanie w tle podczas startu serwera
    task = asyncio.create_task(game_analysis_loop())
    yield
    task.cancel()

app = FastAPI(title="LoL Analytics API", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")

@app.get("/api/state")
async def get_state():
    return current_game_state

@app.post("/api/settings")
async def save_settings(settings: UserSettings):
    app_settings["riot_name"] = settings.riot_name
    app_settings["riot_tag"] = settings.riot_tag
    app_settings["region"] = settings.region
    app_settings["is_configured"] = True
    return {"message": "Zapisano pomyślnie"}

if __name__ == "__main__":
    # Uruchamiamy wyłącznie main.py – serwer i silnik analizy działają razem!
    uvicorn.run(app, host="127.0.0.1", port=8000)