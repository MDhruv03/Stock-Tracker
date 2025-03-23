import asyncpg
import asyncio
from flask import Flask, render_template,request, redirect, url_for, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, current_user,login_user
from models import db,User
from auth import auth  # adjust the import path if necessary

# -------------------------------
# Initialize Flask App
# -------------------------------
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://neondb_owner:npg_2VY3IFQqtPlj@ep-bitter-tooth-a5v8si2g-pooler.us-east-2.aws.neon.tech/neondb"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "supersecretkey"

# -------------------------------
# Initialize Database
# -------------------------------
db.init_app(app) 
app.register_blueprint(auth)
# -------------------------------
# Initialize Flask-Login
# -------------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    from models import User  # Ensure this import works; adjust path if needed
    return User.query.get(int(user_id))

# -------------------------------
# Database Credentials for Async Operations
# -------------------------------
DB_URL = app.config["SQLALCHEMY_DATABASE_URI"]

# -------------------------------
# Define a Login Route
# -------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        from models import User
        user = User.query.first()
        if user:
            from flask_login import login_user
            login_user(user)
            return redirect(url_for("view_portfolio"))
        else:
            return "No user found, please create a user."
    return render_template("login.html")  # <-- Renders the proper template
