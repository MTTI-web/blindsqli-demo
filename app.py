import sqlite3
from flask import Flask, request, render_template

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        # VULNERABLE SQL QUERY: Directly concatenating user input
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"

        try:
            cursor.execute(query)
            user = cursor.fetchone()
        except sqlite3.OperationalError:
            user = None  # Fails gracefully on syntax errors from bad injection

        conn.close()

        if user:
            return render_template("dashboard.html", username=user["username"])
        else:
            error = "Invalid student ID or password."

    return render_template("login.html", error=error)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
