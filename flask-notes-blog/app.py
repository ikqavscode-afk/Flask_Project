import os
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///notes.db")
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-secret-key"
)  # нужен для session и токенов
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(200), nullable=True)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    def generate_token(self):
        s = URLSafeTimedSerializer(app.config["SECRET_KEY"])
        return s.dumps({"user_id": self.id})


def login_required(view):
    """Пускает дальше только вошедших пользователей."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Войдите, чтобы увидеть заметки")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/notes", methods=["GET", "POST"])
@login_required
def notes():
    if request.method == "POST":
        title = request.form["title"]
        subtitle = request.form["subtitle"]
        text = request.form["text"]
        note = Notes(
            title=title,
            subtitle=subtitle,
            text=text,
            user_id=session["user_id"],
        )
        db.session.add(note)
        db.session.commit()
        return redirect(url_for("notes"))
    notes = Notes.query.filter_by(user_id=session["user_id"]).all()
    return render_template("notes.html", notes=notes)


@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            flash("Пользователь с таким логином или email уже существует")
            return redirect(url_for("register"))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Регистрация прошла успешно, теперь войдите")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["token"] = user.generate_token()
            flash(f"Добро пожаловать, {user.username}!")
            return redirect(url_for("index"))
        else:
            flash("Неверный логин или пароль")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Вы вышли из аккаунта")
    return redirect(url_for("home"))


if __name__ == "__main__":
    # Отладчик даёт выполнить код на сервере, поэтому включается только явно: FLASK_DEBUG=1
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
