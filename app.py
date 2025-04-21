from flask import Flask, jsonify, request
import pymysql
import json

app = Flask(__name__)

# Datenbankverbindung
conn = pymysql.connect(
    host="localhost",
    user="nostradamus_user",
    password="Nktd86%50",
    database="NostradamusGPT",
    cursorclass=pymysql.cursors.DictCursor
)

# Einzelner Quatrain abrufen
@app.route("/quatrain/<int:century>/<int:number>", methods=["GET"])
def get_quatrain(century, number):
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM quatrains WHERE century=%s AND quatrain_number=%s",
            (century, number)
        )
        result = cursor.fetchone()
    return jsonify(result if result else {"error": "not found"})

# Suche nach Symbol
@app.route("/symbol/<string:symbol>", methods=["GET"])
def get_by_symbol(symbol):
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM quatrains WHERE symbols LIKE %s",
            [f'%{symbol}%']
        )
        result = cursor.fetchall()
    return jsonify(result)

# Einzelner Quatrain einfügen
@app.route("/quatrain", methods=["POST"])
def insert_quatrain():
    data = request.get_json()
    with conn.cursor() as cursor:
        sql = """
        INSERT INTO quatrains
        (century, quatrain_number, text_original, text_modern, symbols, themes,
         astrological_refs, chronotopes, historical_refs, linguistic_features, semantic_tags)
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

# Mehrere Quatrains auf einmal einfügen
@app.route("/insert_batch", methods=["POST"])
def insert_batch():
    data = request.get_json()
    inserted = 0
    for q in data:
        try:
            with conn.cursor() as cursor:
                sql = """
                INSERT IGNORE INTO quatrains
                (century, quatrain_number, text_original, text_modern, symbols, themes,
                 astrological_refs, chronotopes, historical_refs, linguistic_features, semantic_tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    q["century"], q["quatrain_number"], q["text_original"], q["text_modern"],
                    json.dumps(q["symbols"]), json.dumps(q["themes"]), json.dumps(q["astrological_refs"]),
                    json.dumps(q["chronotopes"]), json.dumps(q["historical_refs"]),
                    json.dumps(q["linguistic_features"]), json.dumps(q["semantic_tags"])
                ))
            conn.commit()
            inserted += 1
        except Exception as e:
            print(f"Fehler bei Q{q.get('century')}.{q.get('quatrain_number')}: {e}")
    return jsonify({"message": f"{inserted} Quatrains eingefügt"})
