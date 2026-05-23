from flask import Flask, render_template, request, redirect, session, flash
import os
import sqlite3
import mysql.connector
from werkzeug.utils import secure_filename
import numpy as np

app = Flask(__name__)
app.secret_key = "SkinCancerAI_SecretKey_2025"
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
app.config["MODEL_PATH"]    = os.path.join("model", "vgg16_skin_cancer.h5")

_model = None

def get_model():
    global _model
    if _model is None:
        from tensorflow.keras.models import load_model
        _model = load_model(app.config["MODEL_PATH"], compile=False)
    return _model

def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="skin_cancer_db",
            connect_timeout=2
        )
    except Exception:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                password TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                age INTEGER,
                result TEXT,
                probability FLOAT,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("SELECT * FROM users WHERE username='admin'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password) VALUES ('admin', '1234')")
        conn.commit()
        return conn

def close_db(db):
    db.close()

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db_connection()
        if hasattr(db, 'cursor'): 
            if isinstance(db, sqlite3.Connection):
                cursor = db.cursor() 
                cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                               (username, password))
            else:
                cursor = db.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s",
                               (username, password))
            
            user = cursor.fetchone()
            db.close()

        if user:
            session["user"] = username
            flash("Connexion réussie ✓", "success")
            return redirect("/dashboard")
        else:
            flash("Identifiants incorrects ✗", "danger")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    try:
        db = get_db_connection()
        if isinstance(db, sqlite3.Connection):
            cursor = db.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM patients")
            total = cursor.fetchone()["total"]
            cursor.execute("SELECT * FROM patients ORDER BY created_at DESC LIMIT 3")
            recents = cursor.fetchall()
        else:
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) AS total FROM patients")
            total = cursor.fetchone()["total"]
            cursor.execute("SELECT * FROM patients ORDER BY created_at DESC LIMIT 3")
            recents = cursor.fetchall()
        db.close()
    except Exception as e:
        print(f"DB Error: {e}")
        total   = 0
        recents = []
    return render_template("dashboard.html", total=total, recents=recents)


@app.route("/predict", methods=["GET", "POST"])
def predict():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        try:
            name = request.form["name"]
            age  = request.form["age"]
            file = request.files["image"]

            if file.filename == "":
                flash("Veuillez choisir une image.", "warning")
                return redirect("predict")

            filename  = secure_filename(file.filename)
            upload_dir = app.config["UPLOAD_FOLDER"]
            os.makedirs(upload_dir, exist_ok=True)
            path = os.path.join(upload_dir, filename)
            file.save(path)

            from tensorflow.keras.preprocessing import image as keras_image
            img = keras_image.load_img(path, target_size=(224, 224))
            img_array = keras_image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0) / 255.0

            mdl  = get_model()
            pred = float(mdl.predict(img_array)[0][0])
            result      = "Malin" if pred >= 0.5 else "Bénin"
            probability = pred


            db = get_db_connection()
            if isinstance(db, sqlite3.Connection):
                cursor = db.cursor()
                cursor.execute(
                    "INSERT INTO patients (name, age, result, probability, image_path) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (name, age, result, probability, path)
                )
            else:
                cursor = db.cursor()
                cursor.execute(
                    "INSERT INTO patients (name, age, result, probability, image_path) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (name, age, result, probability, path)
                )
            db.commit()
            db.close()

            img_display = path.replace("\\", "/")
            return render_template(
                "result.html",
                result=result,
                prob=round(probability * 100, 2),
                img=img_display,
                name=name,
                age=age
            )

        except Exception as e:
            flash(f"Erreur système ✗ : {e}", "danger")
            return redirect("predict")

    return render_template("predict.html")


@app.route("/patients")
def patients():
    if "user" not in session:
        return redirect("/")

    db = get_db_connection()
    if isinstance(db, sqlite3.Connection):
        cursor = db.cursor()
        cursor.execute("SELECT * FROM patients ORDER BY created_at DESC")
    else:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM patients ORDER BY created_at DESC")
        
    data = cursor.fetchall()
    db.close()

    return render_template("patients.html", patients=data)


@app.route("/logout")
def logout():
    session.clear()
    flash("Déconnexion réussie.", "info")
    return redirect("/")


if __name__ == "__main__":
    os.makedirs("static/uploads", exist_ok=True)
    app.run(debug=True)
