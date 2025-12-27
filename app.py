import sqlite3
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"  # needed for sessions

def get_db():
    conn = sqlite3.connect("todo.db")
    conn.row_factory = sqlite3.Row  # <--- add this line
    return conn


# --- Create tables ---
with get_db() as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed_password = generate_password_hash(password)

        db = get_db()
        try:
            db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            db.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Username already exists")

    return render_template("register.html")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
@app.route("/", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    if request.method == "POST":
        task = request.form.get("task")
        if task:
            db.execute("INSERT INTO tasks (name, user_id) VALUES (?, ?)", (task, session["user_id"]))
            db.commit()
        return redirect("/")

    tasks = db.execute("SELECT * FROM tasks WHERE user_id=?", (session["user_id"],)).fetchall()
    return render_template("index.html", tasks=tasks)

@app.route("/delete/<int:id>")
def delete(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    db.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (id, session["user_id"]))
    db.commit()
    return redirect("/")

@app.route("/toggle/<int:id>", methods=["POST"])
def toggle(id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    task = db.execute("SELECT completed FROM tasks WHERE id=? AND user_id=?", (id, session["user_id"])).fetchone()
    if not task:
        return jsonify({"error": "Task not found"}), 404

    new_status = 0 if task[0] else 1
    db.execute("UPDATE tasks SET completed=? WHERE id=? AND user_id=?", (new_status, id, session["user_id"]))
    db.commit()
    return jsonify({"completed": new_status})
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
