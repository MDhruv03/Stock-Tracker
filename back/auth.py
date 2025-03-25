from flask import Blueprint, request, redirect, url_for, render_template, flash, current_app
from flask_login import login_user, logout_user, login_required
from models import User, Broker  # Using raw-SQL models

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password")
        
        if not name or not password:
            flash("Username and password are required")
            return redirect(url_for("auth.login"))
        
        # Fetch user directly from DB using raw SQL
        user = User.fetch_user_by_name(name)

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("portfolio.view_portfolio"))

        flash("Invalid credentials")
        return redirect(url_for("auth.login"))
    
    return render_template("login.html")

@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]
        brokerage_id = request.form.get("brokerage")
        
        if not brokerage_id:
            flash("Please select a brokerage.")
            return redirect(url_for("auth.signup"))
        
        # Fetch all brokers using raw SQL to validate the brokerage selection.
        brokers = Broker.fetch_all_brokers()
        valid_ids = [broker["brokerage_id"] for broker in brokers]
        
        if int(brokerage_id) not in valid_ids:
            flash("Invalid brokerage selected.")
            return redirect(url_for("auth.signup"))
        
        # Check if user already exists
        existing_user = User.fetch_user_by_name(name)
        if existing_user:
            flash("Username already taken, try another one.")
            return redirect(url_for("auth.signup"))
        
        # Create user (Raw SQL Insert)
        User.create_user(name, password, brokerage_id)
        
        flash("Account created! You can now log in.")
        return redirect(url_for("auth.login"))
    
    # For GET requests, fetch brokers to display in the signup form.
    brokers = Broker.fetch_all_brokers()
    return render_template("signup.html", brokers=brokers)

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
