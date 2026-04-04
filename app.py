import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, render_template, redirect, url_for, session

app = Flask(__name__)

# A secret key is required by Flask to encrypt session cookies
app.secret_key = "super_secret_exhibition_key"

# Your Neon Database Connection String
DATABASE_URL = "postgresql://neondb_owner:npg_xp2YeLlmz0ta@ep-tiny-heart-a1gefso0-pooler.ap-southeast-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require"

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    """Creates the necessary tables in the Postgres database on startup."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    ''')
    
    # Create messages table for XSS demo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY, 
            content TEXT
        )
    ''')
    
    # Insert the admin user if they don't exist
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password) VALUES ('admin', 'password123')")
        
    conn.commit()
    cursor.close()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def login():
    # If the user is already logged in, redirect them immediately to the dashboard
    if "username" in session:
        return redirect(url_for("dashboard"))
        
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        # VULNERABLE SQL QUERY: Directly concatenating user input for SQLi demo
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"

        try:
            cursor.execute(query)
            user = cursor.fetchone()
        except psycopg2.errors.SyntaxError:
            conn.rollback()
            user = None

        cursor.close()
        conn.close()

        if user:
            # Set the session variable to mark the user as logged in
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    # If already logged in, redirect to dashboard
    if "username" in session:
        return redirect(url_for("dashboard"))
        
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username already exists securely
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            error = "Username already exists."
        else:
            # Insert new user securely (You could make this vulnerable too, but usually login is enough for the demo)
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            cursor.close()
            conn.close()
            return render_template("login.html", success="Registration successful! Please log in.")
            
        cursor.close()
        conn.close()
        
    return render_template("register.html", error=error)

@app.route("/dashboard")
def dashboard():
    # Protect dashboard route from logged-out users
    if "username" not in session:
        return redirect(url_for("login"))
        
    username = session["username"]
    messages = []
    
    # Only fetch tickets if the logged-in user is 'admin'
    if username == "admin":
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM messages ORDER BY id DESC")
        messages = cursor.fetchall()
        cursor.close()
        conn.close()
        
    return render_template("dashboard.html", username=username, messages=messages)

@app.route("/delete_ticket/<int:ticket_id>", methods=["POST"])
def delete_ticket(ticket_id):
    # Ensure only the admin can delete tickets
    if session.get("username") != "admin":
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE id = %s", (ticket_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    # Clear the session to log out
    session.clear()
    return redirect(url_for("login"))

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    success = False
    if request.method == "POST":
        content = request.form["content"]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (content) VALUES (%s)", (content,))
        conn.commit()
        cursor.close()
        conn.close()
        success = True
        
    return render_template("feedback.html", success=success)

# Initialize database tables before the first request is processed
@app.before_request
def setup():
    if not hasattr(app, 'db_initialized'):
        init_db()
        app.db_initialized = True

if __name__ == "__main__":
    app.run(debug=True, port=5001)