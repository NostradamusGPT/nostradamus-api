from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import os
import pymysql

app = FastAPI(title="NostradamusGPT API", version="1.0.0")

# --- DB-Verbindung ---
conn = pymysql.connect(
    host="maglev.proxy.rlwy.net",
    port=30020,
    user="root",
    password="YlXGHgmEYePCMuIEiXndztrBjmaPdehg",
    database="railway",
    cursorclass=pymysql.cursors.DictCursor
)

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

# --- JSON-Dateipfad ---
JSON_PATH = "initial_quatrains.json"

# --- Root-Check ---
@app.get("/")
def read_root():
    return {"status": "Nostradamus API online"}

# --- Alle Quatrains aus MySQL abrufen ---
@app.get("/quatrains", response_model=List[dict])
def get_all_quatrains():
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM quatrains ORDER BY century, quatrain_number")
        result = cursor.fetchall()
    return result

# --- Einzelnen Quatrain holen ---
@app.get("/quatrain/{century}/{number}", response_model=dict)
def get_quatrain(century: int, number: int):
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM quatrains WHERE century=%s AND quatrain_number=%s", (century, number))
        result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Quatrain nicht gefunden")
    return result

# --- Suche nach Symbol ---
@app.get("/symbol/{symbol}", response_model=List[dict])
def get_by_symbol(symbol: str):
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM quatrains WHERE symbols LIKE %s", (f'%{symbol}%'))
        result = cursor.fetchall()
    return result

# --- Neuen Quatrain speichern ---
@app.post("/quatrain", response_model=dict)
def insert_quatrain(q: Quatrain):
    with conn.cursor() as cursor:
        sql = """
        REPLACE INTO quatrains
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
    return {"message": "Quatrain erfolgreich gespeichert (oder ersetzt)"}

# --- GET + POST: JSON-Datei in MySQL importieren ---
@app.api_route("/init-data", methods=["GET", "POST"])
def init_data_from_json():
    if not os.path.exists(JSON_PATH):
        raise HTTPException(status_code=404, detail="initial_quatrains.json nicht gefunden")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fehler beim Lesen der JSON-Datei: {e}")

    with conn.cursor() as cursor:
        for entry in data:
            try:
                cursor.execute("""
                    REPLACE INTO quatrains (century, quatrain_number, text_original, text_modern,
                    symbols, themes, astrological_refs, chronotopes, historical_refs,
                    linguistic_features, semantic_tags)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    entry["century"], entry["quatrain"], entry["text"], entry["text"],
                    json.dumps(entry.get("symbols", [])),
                    json.dumps(entry.get("clusters", [])),
                    "[]", "[]", "[]", "[]", "[]"
                ))
            except Exception as e:
                print("Fehler bei Eintrag:", entry)
                raise HTTPException(status_code=500, detail=f"Fehler beim Einfügen in die Datenbank: {e}")
        conn.commit()

    return JSONResponse(content={"message": f"{len(data)} Quatrains erfolgreich in die MySQL-Datenbank geladen (mit REPLACE INTO)."})
