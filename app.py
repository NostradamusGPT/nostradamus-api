from flask import Flask, jsonify, request
from flask_cors import CORS
import pymysql
import json
import os

app = Flask(__name__)
CORS(app)

# Verbindung zur Railway-MySQL-Datenbank
conn = pymysql.connect(
    host="maglev.proxy.rlwy.net",
    port=30020,
    user="root",
    password="YlXGHgmEYePCMuIEiXndztrBjmaPdehg",
    database="railway",
    cursorclass=pymysql.cursors.DictCursor
)

@app.route("/quatrain/<int:century>/<int:number>", methods=["GET"])
def get_quatrain(century, number):
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM quatrains WHERE century=%s AND quatrain_number=%s", (century, number)
        )
        result = cursor.fetchone()
    return jsonify(result if result else {"error": "not found"})

@app.route("/symbol/<string:symbol>", methods=["GET"])
def get_by_symbol(symbol):
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM quatrains WHERE symbols LIKE %s", [f'%{symbol}%'])
        result = cursor.fetchall()
    return jsonify(result)

@app.route("/quatrains", methods=["GET"])
def get_all_quatrains():
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM quatrains ORDER BY century, quatrain_number")
        result = cursor.fetchall()
    return jsonify(result)

@app.route("/quatrain", methods=["POST"])
def insert_quatrain():
    data = request.get_json()
    with conn.cursor() as cursor:
        sql = """
        INSERT INTO quatrains
        (century, quatrain_number, text_original, text_modern, symbols, themes, astrological_refs,
         chronotopes, historical_refs, linguistic_features, semantic_tags)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            data["century"], data["quatrain_number"], data["text_original"], data["text_modern"],
            json.dumps(data["symbols"]), json.dumps(data["themes"]), json.dumps(data["astrological_refs"]),
            json.dumps(data["chronotopes"]), json.dumps(data["historical_refs"]),
            json.dumps(data["linguistic_features"]), json.dumps(data["semantic_tags"])
        ))
        conn.commit()
    return jsonify({"message": "Quatrain gespeichert"})

@app.route("/init-data", methods=["POST"])
def init_data():
    # Stelle sicher, dass die Datei im gleichen Verzeichnis liegt
    json_path = os.path.join(os.path.dirname(__file__), "initial_quatrains.json")
    with open(json_path, "r") as f:
        data = json.load(f)

    with conn.cursor() as cursor:
        for entry in data:
            cursor.execute("""
                INSERT INTO quatrains (century, quatrain_number, text_original, text_modern,
                symbols, themes, astrological_refs, chronotopes, historical_refs,
                linguistic_features, semantic_tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                entry["century"], entry["quatrain_number"], entry["text_original"], entry["text_modern"],
                json.dumps(entry["symbols"]), json.dumps(entry["themes"]), json.dumps(entry["astrological_refs"]),
                json.dumps(entry["chronotopes"]), json.dumps(entry["historical_refs"]),
                json.dumps(entry["linguistic_features"]), json.dumps(entry["semantic_tags"])
            ))
    conn.commit()
    return jsonify({"message": "Alle Daten erfolgreich geladen"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
