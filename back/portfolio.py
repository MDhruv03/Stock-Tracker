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

# ✅ Route for fetching 52-week High/Low Stocks
@portfolio.route("/high-low-stocks", methods=["GET"])
def high_low_stocks():
    """ Fetch and return stocks based on their 52-week high/low values """
    query = "SELECT * FROM get_high_low_stocks();"
    stocks = fetch_data(query)
    
    # Convert the result into a list of dictionaries for JSON response
    stocks_data = [
        {
            "ticker": stock["ticker"],
            "name": stock["name"],
            "high_52": float(stock["high_52"]),
            "low_52": float(stock["low_52"])
        }
        for stock in stocks
    ]
    
    return jsonify(stocks_data)  # ✅ Returns JSON response

# ✅ Route for filtering stocks
@portfolio.route("/filter-stocks", methods=["POST"])
def filter_stocks():
    """ Filter stocks based on user-provided criteria. """
    data = request.json
    min_eps = data.get("min_eps", 0)
    max_pe = data.get("max_pe", 100)

    query = "SELECT * FROM filter_stocks(%s, %s);"
    stocks = fetch_data(query, (min_eps, max_pe))
    
    # Convert the result into a list of dictionaries for JSON response
    filtered_stocks = [
        {
            "ticker": stock["ticker"],
            "name": stock["name"],
            "eps_growth": float(stock["eps_growth"]),
            "pe_ratio": float(stock["pe_ratio"])
        }
        for stock in stocks
    ]
    
    return jsonify(filtered_stocks)  # ✅ Returns JSON response
