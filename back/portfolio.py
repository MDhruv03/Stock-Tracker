from flask import Blueprint, render_template, current_app, redirect, url_for, jsonify, request
from flask_login import login_required, current_user
import subprocess
import sys

portfolio = Blueprint("portfolio", __name__)

def fetch_data(query, params=None, fetch_one=False):
    """ Fetch data from PostgreSQL using connection pooling. """
    conn = current_app.config["DB_POOL"].getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            column_names = [desc[0] for desc in cur.description]  # Get column names

            if fetch_one:
                row = cur.fetchone()
                return dict(zip(column_names, row)) if row else None
            else:
                rows = cur.fetchall()
                return [dict(zip(column_names, row)) for row in rows]  # Convert to list of dicts
    finally:
        current_app.config["DB_POOL"].putconn(conn)  # Return connection to the pool

@portfolio.route("/")
@login_required
def view_portfolio():
    """Fetch user's portfolio and render it."""
    user_id = current_user.user_id
    query = "SELECT * FROM get_user_portfolio(%s);"
    user_stocks = fetch_data(query, (user_id,))

    return render_template("portfolio.html", stocks=user_stocks)

@portfolio.route("/buy-stocks")
@login_required
def buy_stocks():
    """Fetch all available stocks and render the buy stocks page."""
    query = "SELECT ticker, name, price, high_52, low_52 FROM Stock;"
    all_stocks = fetch_data(query)

    return render_template("buy_stocks.html", stocks=all_stocks)

@portfolio.route("/update-prices", methods=["POST"])
@login_required
def update_prices():
    """Trigger stock price update and refresh the page."""
    try:
        # ✅ Run update_prices.py using the same Python interpreter
        subprocess.run([sys.executable, "update_prices.py"], check=True)
        print("✅ Stock prices updated successfully!")
    except Exception as e:
        print(f"❌ Error updating prices: {e}")
    
    return redirect(url_for("portfolio.view_portfolio"))  # ✅ Refresh portfolio page

@portfolio.route("/allocation")
@login_required
def get_high_allocations():
    """Fetch stocks where allocation percentage > 50%"""
    user_id = current_user.user_id
    query = """
    SELECT user_id, stock_ticker AS stock_id, 
           (stock_value / total_value) * 100 AS allocation_percentage
    FROM (
        SELECT t.user_id, t.stock_ticker, 
               SUM(t.quantity * s.price) AS stock_value, 
               (SELECT SUM(quantity * price) FROM Transactions 
                JOIN Stock ON Transactions.stock_ticker = Stock.ticker 
                WHERE user_id = t.user_id) AS total_value
        FROM Transactions t
        JOIN Stock s ON t.stock_ticker = s.ticker
        GROUP BY t.user_id, t.stock_ticker
    ) AS portfolio_alloc
    WHERE (stock_value / total_value) * 100 > 50;
    """
    
    results = fetch_data(query, (user_id,))
    return jsonify(results)





