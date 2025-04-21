from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pymysql
import os
import json

# --- FastAPI-Instanz ---
app = FastAPI(title="NostradamusGPT API", version="1.0.0")

# --- Pydantic-Modell ---
class Quatrain(BaseModel):
    id: Optional[int]
    century: int
    quatrain: int
    text: str
    symbols: List[str] = []
    clusters: List[str] = []
    year_hint: Optional[str] = ""
    notes: Optional[str] = ""

# --- JSON-Fallback-Laden (nur lokal) ---
quatrains_db: List[Quatrain] = []
JSON_PATH = "initial_quatrains.json"

if os.path.exists(JSON_PATH):
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            quatrains_db = [Quatrain(**item) for item in data]
            print(f"{len(quatrains_db)} Quatrains geladen (JSON-Fallback).")
    except Exception as e:
        print(f"Fehler beim Laden von {JSON_PATH}: {e}")

# --- MySQL-Verbindung über Railway ---
conn = pymysql.connect(
    host=os.getenv("MYSQLHOST", "maglev.proxy.rlwy.net"),
    user=os.getenv("MYSQLUSER", "root"),
    password=os.getenv("MYSQLPASSWORD", "YlXGHgmEYePCMuIEiXndztrBjmaPdehg"),
    database=os.getenv("MYSQLDATABASE", "railway"),
    port=int(os.getenv("MYSQLPORT", 30020)),
    cursorclass=pymysql.cursors.DictCursor
)

# --- API-Root ---
@app.get("/")
def read_root():
    return {"status": "NostradamusGPT API online 🎯"}

# --- Alle Quatrains abrufen ---
@app.get("/quatrains", response_model=List[dict])
def get_all_quatrains():
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM quatrains ORDER BY century, quatrain_number")
        return cursor.fetchall()

# --- Einzelner Quatrain nach Jahrhundert & Nummer ---
@app.get("/quatrain/{century}/{number}", response_model=dict)
def get_quatrain(century: int, number: int):
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM quatrains WHERE century=%s AND quatrain_number=%s", (century, number))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Quatrain nicht gefunden")
        return result

# --- Suche nach Symbolen ---
@app.get("/symbol/{symbol}", response_model=List[dict])
def get_by_symbol(symbol: str):
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM quatrains WHERE symbols LIKE %s", (f'%{symbol}%',))
        return cursor.fetchall()

# --- Eintrag eines neuen Quatrains ---
@app.post("/quatrain", response_model=dict)
def insert_quatrain(q: Quatrain):
    with conn.cursor() as cursor:
        sql = """
        INSERT INTO quatrains
        (century, quatrain_number, text_original, text_modern, symbols, themes,
         astrological_refs, chronotopes, historical_refs, linguistic_features, semantic_tags)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            q.century, q.quatrain, q.text, q.text,
            json.dumps(q.symbols), json.dumps(q.clusters),
            "[]", "[]", "[]", "[]", "[]"
        ))
        conn.commit()
    return {"message": "Quatrain erfolgreich gespeichert"}

# --- Initial-Import aus JSON-Datei ---
@app.post("/init-data")
def init_data_from_json():
    if not os.path.exists(JSON_PATH):
        raise HTTPException(status_code=404, detail="initial_quatrains.json nicht gefunden")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    with conn.cursor() as cursor:
        for entry in data:
            cursor.execute("""
                INSERT INTO quatrains (century, quatrain_number, text_original, text_modern,
                symbols, themes, astrological_refs, chronotopes, historical_refs,
                linguistic_features, semantic_tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                entry["century"], entry["quatrain"], entry["text"], entry["text"],
                json.dumps(entry["symbols"]), json.dumps(entry["clusters"]),
                "[]", "[]", "[]", "[]", "[]"
            ))
        conn.commit()

    return {"message": f"{len(data)} Quatrains erfolgreich importiert"}
