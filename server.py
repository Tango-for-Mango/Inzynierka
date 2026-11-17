from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse  # NOWY IMPORT
import uvicorn

app = FastAPI(title="LoL Analytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

current_game_state = {
    "status": "Oczekiwanie na dołączenie do meczu...",
    "player_gold": 0,
    "threats": ["Brak wykrytych zagrożeń (test interfejsu)"],
    "income_advice": None
}

# NOWY ENDPOINT: Udostępnia interfejs w przeglądarce pod głównym adresem
@app.get("/")
async def serve_frontend():
    # Upewnij się, że ścieżka do pliku odpowiada Twojej strukturze folderów
    return FileResponse("frontend/index.html")

@app.get("/api/state")
async def get_state():
    return current_game_state

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)