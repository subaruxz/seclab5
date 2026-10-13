
from flask import Flask, request, jsonify
import sqlite3
from pathlib import Path

app = Flask(__name__)

DB_PATH = Path(__file__).with_name("users.db")


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)


@app.route("/api/users", methods=["POST"])
def create_user():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Ожидается JSON-объект"}), 400

    name = data.get("name")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Имя обязательно"}), 400

    if len(name) > 100:
        return jsonify({"error": "Имя слишком длинное"}), 400

    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO users (name) VALUES (?)",
            (name.strip(),)
        )
        user_id = cursor.lastrowid

    return jsonify({"id": user_id, "name": name.strip()}), 201


@app.route("/api/users", methods=["GET"])
def get_users():
    with get_db() as db:
        rows = db.execute(
            "SELECT id, name FROM users ORDER BY id"
        ).fetchall()

    users = [dict(row) for row in rows]
    return jsonify(users), 200


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    with get_db() as db:
        cursor = db.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,)
        )

        if cursor.rowcount == 0:
            return jsonify({"error": "Пользователь не найден"}), 404

    return jsonify({"message": "Пользователь удалён"}), 200


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=False)
