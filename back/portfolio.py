from flask import Blueprint, render_template, current_app, redirect, url_for, jsonify, request,jsonify
from flask_login import login_required, current_user
import subprocess
import sys
import os
import pandas as pd
import psycopg2
import yfinance as yf


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

    if user_stocks:
        total_investment = user_stocks[0]["total_portfolio_investment"]
        total_current_value = user_stocks[0]["total_portfolio_value"]  # Use the same variable
        total_pnl = user_stocks[0]["total_portfolio_pnl"]
    else:
        total_investment = 0
        total_current_value = 0  # Use the correct variable name
        total_pnl = 0


    return render_template("portfolio.html", stocks=user_stocks, 
                           total_investment=total_investment, 
                           total_current_value=total_current_value, 
                           total_pnl=total_pnl)


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
        script_path = os.path.join(os.getcwd(), "back", "update_prices.py")
        subprocess.run([sys.executable, script_path], check=True)
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

@portfolio.route("/portfolio/history")
@login_required
def get_historical_portfolio_value():
    user_id = current_user.user_id

    query = """
        WITH DailyHoldings AS (
            SELECT
                t.timestamp::DATE AS date,
                t.user_id,
                t.stock_ticker,
                SUM(
                    CASE 
                        WHEN t.type = 'BUY' THEN t.quantity 
                        WHEN t.type = 'SELL' THEN -t.quantity 
                        ELSE 0 
                    END
                ) OVER (PARTITION BY t.user_id, t.stock_ticker ORDER BY t.timestamp) AS quantity
            FROM Transactions t
            WHERE t.user_id = %s
        ),
        DailyPortfolio AS (
            SELECT 
                date,
                user_id,
                SUM(quantity * s.price) AS portfolio_value
            FROM DailyHoldings dh
            JOIN Stock s ON dh.stock_ticker = s.ticker
            WHERE quantity > 0
            GROUP BY date, user_id
        )
        SELECT date, user_id, portfolio_value
        FROM DailyPortfolio
        ORDER BY date;
    """
    historical_data = fetch_data(query, (user_id,))

    # Convert to JSON-friendly format: date as string and Decimal to float
    history = [
        {
            "date": row["date"].strftime("%Y-%m-%d"),
            "user_id": row["user_id"],
            "portfolio_value": float(row["portfolio_value"])
        }
        for row in historical_data
    ]

    return jsonify({"history": history})

@portfolio.route('/portfolio/transactions_history', methods=['GET'])
def get_transaction_history():
    user_id = current_user.user_id  # Using attribute access
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    query = """
    WITH TransactionHistory AS (
        SELECT
            t.transaction_id,
            t.timestamp::DATE AS date,
            t.stock_ticker,
            t.type,
            t.quantity,
            t.price,
            (t.quantity * t.price) AS transaction_amount
        FROM Transactions t
        WHERE t.user_id = %s
    ),
    RealizedPnl AS (
        SELECT 
            t.stock_ticker,
            SUM(
                CASE 
                    WHEN t.type = 'SELL' THEN (t.quantity * (t.price - p.avg_price))
                    ELSE 0 
                END
            ) AS realized_pnl
        FROM Transactions t
        JOIN Portfolio p ON t.stock_ticker = p.stock_ticker AND t.user_id = p.user_id
        WHERE t.user_id = %s
        GROUP BY t.stock_ticker
    ),
    UnrealizedPnl AS (
        SELECT 
            p.stock_ticker,
            (p.quantity * (s.price - p.avg_price)) AS unrealized_pnl
        FROM Portfolio p
        JOIN Stock s ON p.stock_ticker = s.ticker
        WHERE p.user_id = %s
    )
    SELECT th.*, COALESCE(rp.realized_pnl, 0) AS realized_pnl, COALESCE(up.unrealized_pnl, 0) AS unrealized_pnl
    FROM TransactionHistory th
    LEFT JOIN RealizedPnl rp ON th.stock_ticker = rp.stock_ticker
    LEFT JOIN UnrealizedPnl up ON th.stock_ticker = up.stock_ticker
    ORDER BY th.date DESC
    LIMIT 15;
"""


    transactions = fetch_data(query, (user_id, user_id, user_id))

    result = []
    for row in transactions:
        result.append({
            "transaction_id": row["transaction_id"],
            "date": row["date"].strftime('%Y-%m-%d'),
            "stock_ticker": row["stock_ticker"],
            "type": row["type"],
            "quantity": row["quantity"],
            "price": float(row["price"]),
            "transaction_amount": float(row["transaction_amount"]),
            "realized_pnl": float(row["realized_pnl"]),
            "unrealized_pnl": float(row["unrealized_pnl"])
        })

    return jsonify(result)







