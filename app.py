from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv("dotenv.env")

DATABASE = "forum.db"

app.secret_key = os.getenv("SECRET_KEY")


def get_db():
    conn = sqlite3.connect(DATABASE)
    curs = conn.cursor()

    curs.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    """)
    curs.execute("""
    CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    content TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()

get_db()


@app.route('/')
def index():
    return render_template("login.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect(DATABASE)
        curs = conn.cursor()

        curs.execute(
    "SELECT id, password FROM users WHERE username = ?",
    (username,)
)
        user = curs.fetchone()  # user[0] = id, user[1] = password

        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]       # id réel
            session["username"] = username
            return redirect("/index")
        else:
            return "Identifiants incorrects"

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect(DATABASE)
        curs = conn.cursor()

        curs.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        )

        if curs.fetchone():
            conn.close()
            return "Utilisateur déjà existant"

        curs.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/index", methods=["POST","GET"])
def index_html():
    if "user_id" not in session:
        return redirect("/login")
        
        
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()

    if request.method == "POST":
        mess = request.form.get("message")
        if mess:
            curs.execute(
                "INSERT INTO messages (content, user_id) VALUES (?, ?)",
                (mess, session["user_id"])
            )
            conn.commit()

    curs.execute("""
        SELECT messages.content, messages.created_at, users.username
        FROM messages
        JOIN users ON users.id = messages.user_id
        ORDER BY messages.created_at DESC
    """)

    messages = curs.fetchall()
    conn.close()

    return render_template("index.html", messages=messages)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/forum", methods=["POST"])
def forum():
    if request.method == "POST":
        mess = request.form.get("message")
        conn = sqlite3.connect(DATABASE)
        curs = conn.cursor()
        curs.execute(
            "INSERT INTO messages (content, user_id) VALUES (?,?)",
            (mess, session["user_id"])
        )
        conn.commit()
        conn.close()
        
        return redirect("/index")



if __name__ == '__main__':
    app.run(debug=True)
