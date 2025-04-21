from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import os
import pymysql

app = FastAPI(title="NostradamusGPT API", version="1.0.0")

# --- Pydantic Modell ---
class Quatrain(BaseModel):
    id: Optional[int]
    century: int
    quatrain: int
    text: str
    symbols: List[str] = []
    clusters: List[str] = []
    year_hint: Optional[str] = ""
    notes: Optional[str] = ""

# --- JSON-Import (Backup-Quelle) ---
quatrains_db: List[Quatrain] = []
JSON_PATH = "initial_quatrains.json"

if os.path.exists(JSON_PATH):
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            quatrains_db = [Quatrain(**item) for item in data]
            print(f"{len(quatrains_db)} Quatrains geladen (JSON-Fallback).")
        except Exception as e:
            print(f"Fehler beim Laden von {JSON_PATH}: {e}")

# --- MySQL-Verbindung (Railway) ---
conn = pymysql.connect(
    host="maglev.proxy.rlwy.net",
    port=30020,
    user="root",
    password="YlXGHgmEYePCMuIEiXndztrBjmaPdehg",
    database="railway",
    cursorclass=pymysql.cursors.DictCursor
)

# --- API Routes ---
@app.get("/")
def read_root():
    return {"status": "Nostradamus API online"}

@app.get("/quatrains", response_model=List[dict])
def get_all_quatrains():
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM quatrains ORDER BY century, quatrain_number")
        result = cursor.fetchall()
    return result

@app.get("/quatrain/{century}/{number}", response_model=dict)
def get_quatrain(century: int, number: int):
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM quatrains WHERE century=%s AND quatrain_number=%s", (century, number))
        result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Quatrain nicht gefunden")
    return result

@app.get("/symbol/{symbol}", response_model=List[dict])
def get_by_symbol(symbol: str):
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM quatrains WHERE symbols LIKE %s", (f'%{symbol}%',))
        result = cursor.fetchall()
    return result

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
            q.century, q.quatrain, q.text, q.text,  # text_original = text_modern
            json.dumps(q.symbols), json.dumps(q.clusters), "[]", "[]", "[]", "[]", "[]"
        ))
        conn.commit()
    return {"message": "Quatrain erfolgreich gespeichert"}

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

    return {"message": "Alle JSON-Daten erfolgreich in MySQL geladen"}
