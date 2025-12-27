from flask import Flask, render_template, request, redirect
import sqlite3
from flask import jsonify
app = Flask(__name__)

# Create DB
def get_db():
    return sqlite3.connect("todo.db")

with get_db() as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            completed INTEGER DEFAULT 0
        )
    """)

@app.route("/", methods=["GET", "POST"])
def index():
    db = get_db()

    if request.method == "POST":
        task = request.form.get("task")
        if task:
            db.execute("INSERT INTO tasks (name) VALUES (?)", (task,))
            db.commit()
        return redirect("/")

    tasks = db.execute("SELECT * FROM tasks").fetchall()
    return render_template("index.html", tasks=tasks)

@app.route("/delete/<int:id>")
def delete(id):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ?", (id,))
    db.commit()
    return redirect("/")




@app.route("/toggle/<int:id>", methods=["POST"])
def toggle(id):
    # Use your existing DB connection
    task = db.execute("SELECT completed FROM tasks WHERE id=?", (id,)).fetchone()
    if task is None:
        return jsonify({"error": "Task not found"}), 404

    new_status = 0 if task[0] else 1
    db.execute("UPDATE tasks SET completed=? WHERE id=?", (new_status, id))
    db.commit()
    return jsonify({"completed": new_status})



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
