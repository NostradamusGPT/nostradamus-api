from flask import Flask, jsonify, request
from flask_cors import CORS
import pymysql
import json
import os

app = Flask(__name__)
CORS(app)  # Erlaubt CORS für alle Domains – ideal für API-Zugriffe aus dem Frontend

# Verbindung zur Railway-MySQL-Datenbank
try:
    conn = pymysql.connect(
        host=os.getenv("MYSQL_HOST", "maglev.proxy.rlwy.net"),
        port=int(os.getenv("MYSQL_PORT", 30020)),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "YlXGHgmEYePCMuIEiXndztrBjmaPdehg"),
        database=os.getenv("MYSQL_DATABASE", "railway"),
        cursorclass=pymysql.cursors.DictCursor
    )
except Exception as e:
    app.logger.error(f"Datenbankverbindung fehlgeschlagen: {e}")
    conn = None


@app.route("/")
def index():
    return jsonify({"status": "NostradamusGPT API online"})


@app.route("/quatrain/<int:century>/<int:number>", methods=["GET"])
def get_quatrain(century, number):
    if not conn:
        return jsonify({"error": "Keine Datenbankverbindung"}), 500
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM quatrains WHERE century=%s AND quatrain_number=%s", (century, number))
        result = cursor.fetchone()
    return jsonify(result if result else {"error": "not found"})


@app.route("/symbol/<string:symbol>", methods=["GET"])
def get_by_symbol(symbol):
    if not conn:
        return jsonify({"error": "Keine Datenbankverbindung"}), 500
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM quatrains WHERE symbols LIKE %s", [f'%{symbol}%'])
        result = cursor.fetchall()
    return jsonify(result)


@app.route("/quatrain", methods=["POST"])
def insert_quatrain():
    if not conn:
        return jsonify({"error": "Keine Datenbankverbindung"}), 500
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
