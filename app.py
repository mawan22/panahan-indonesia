from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3, os

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Pastikan folder upload ada
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ================= DATABASE INIT =================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS atlet (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT,
        kategori TEXT,
        foto TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS berita (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        judul TEXT,
        isi TEXT,
        tanggal TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS jadwal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kegiatan TEXT,
        tanggal TEXT,
        lokasi TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS prestasi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT,
        event TEXT,
        juara TEXT,
        tahun TEXT
    )
    """)

    # Admin default
    c.execute("SELECT * FROM user WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO user (username,password) VALUES (?,?)",
                  ("admin", generate_password_hash("admin123")))

    conn.commit()
    conn.close()

# ================= LOGIN =================
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM user WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            login_user(User(user[0]))
            return redirect("/admin")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

# ================= PUBLIC =================
@app.route("/")
def index():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM atlet")
    total_atlet = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM berita")
    total_berita = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM prestasi")
    total_prestasi = c.fetchone()[0]

    conn.close()

    return render_template("index.html",
                           total_atlet=total_atlet,
                           total_berita=total_berita,
                           total_prestasi=total_prestasi)

@app.route("/atlet")
def atlet():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM atlet")
    data = c.fetchall()
    conn.close()
    return render_template("atlet.html", data=data)

@app.route("/berita")
def berita():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM berita ORDER BY id DESC")
    data = c.fetchall()
    conn.close()
    return render_template("berita.html", data=data)

@app.route("/jadwal")
def jadwal():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM jadwal ORDER BY tanggal ASC")
    data = c.fetchall()
    conn.close()
    return render_template("jadwal.html", data=data)

@app.route("/prestasi")
def prestasi():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM prestasi")
    data = c.fetchall()
    conn.close()
    return render_template("prestasi.html", data=data)

@app.route("/kategori/<jenis>")
def kategori(jenis):
    return render_template("kategori.html", jenis=jenis)

# ================= ADMIN =================
@app.route("/admin", methods=["GET","POST"])
@login_required
def admin():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":
        tipe = request.form["tipe"]

        if tipe == "atlet":
            foto = request.files["foto"]
            filename = secure_filename(foto.filename)
            foto.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            c.execute("INSERT INTO atlet (nama,kategori,foto) VALUES (?,?,?)",
                      (request.form["nama"], request.form["kategori"], filename))

        elif tipe == "berita":
            c.execute("INSERT INTO berita (judul,isi,tanggal) VALUES (?,?,?)",
                      (request.form["judul"], request.form["isi"], request.form["tanggal"]))

        elif tipe == "jadwal":
            c.execute("INSERT INTO jadwal (kegiatan,tanggal,lokasi) VALUES (?,?,?)",
                      (request.form["kegiatan"], request.form["tanggal"], request.form["lokasi"]))

        elif tipe == "prestasi":
            c.execute("INSERT INTO prestasi (nama,event,juara,tahun) VALUES (?,?,?,?)",
                      (request.form["nama"], request.form["event"],
                       request.form["juara"], request.form["tahun"]))

        conn.commit()

    # ambil data atlet untuk ditampilkan
    c.execute("SELECT * FROM atlet")
    atlet_data = c.fetchall()

    conn.close()
    return render_template("admin.html", data=atlet_data)

@app.route("/hapus_atlet/<int:id>")
@login_required
def hapus_atlet(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM atlet WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

# ================= RUN =================
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
