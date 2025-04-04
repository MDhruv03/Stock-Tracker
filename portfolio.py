from flask import Blueprint, render_template, current_app, redirect, url_for, jsonify, request,jsonify,flash
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

def execute_query(query, params=None):
    """ Execute a query that doesn't return data (INSERT, UPDATE, DELETE) """
    conn = current_app.config["DB_POOL"].getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        current_app.config["DB_POOL"].putconn(conn)

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
        total_pnl_pct=round(((total_current_value-total_investment)/total_investment)*100,2)
    else:
        total_investment = 0
        total_current_value = 0  # Use the correct variable name
        total_pnl = 0
        total_pnl_pct=0


    return render_template("portfolio.html", stocks=user_stocks, 
                           total_investment=total_investment, 
                           total_current_value=total_current_value, 
                           total_pnl=total_pnl,total_pnl_pct=total_pnl_pct)


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
        script_path = os.path.join(os.getcwd(), "update_prices.py")
        subprocess.run([sys.executable, script_path], check=True)
        print("✅ Stock prices updated successfully!")
    except Exception as e:
        print(f"❌ Error updating prices: {e}")
    
    return redirect(url_for("portfolio.view_portfolio"))  # ✅ Refresh portfolio page

@portfolio.route("/allocation")
@login_required
def get_high_allocations():
    """Fetch all stock allocations as percentages"""
    user_id = current_user.user_id
    query = """
    SELECT 
        stock_ticker AS stock_id, 
        ROUND((stock_value / NULLIF(total_value, 0)) * 100, 2) AS allocation_percentage
    FROM (
        SELECT 
            t.user_id, 
            t.stock_ticker, 
            SUM(t.quantity * s.price) AS stock_value, 
            (SELECT SUM(t2.quantity * s2.price) 
             FROM Transactions t2
             JOIN Stock s2 ON t2.stock_ticker = s2.ticker 
             WHERE t2.user_id = t.user_id) AS total_value
        FROM Transactions t
        JOIN Stock s ON t.stock_ticker = s.ticker
        WHERE t.user_id = %s
        GROUP BY t.user_id, t.stock_ticker
    ) AS portfolio_alloc
    ORDER BY allocation_percentage DESC;
    """
    
    results = fetch_data(query, (user_id,))
    return jsonify(results)


@portfolio.route('/transactions_history', methods=['GET'])
def get_transaction_history():
    user_id = current_user.user_id  # Using attribute access
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # In portfolio.py's get_transaction_history route
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
            t_sell.transaction_id,
            t_sell.quantity * (
                t_sell.price - COALESCE((
                    SELECT SUM(t_buy.quantity * t_buy.price) / NULLIF(SUM(t_buy.quantity), 0)
                    FROM Transactions t_buy
                    WHERE t_buy.user_id = t_sell.user_id
                        AND t_buy.stock_ticker = t_sell.stock_ticker
                        AND t_buy.type = 'BUY'
                        AND t_buy.timestamp <= t_sell.timestamp
                ), 0)
            ) AS realized_pnl
        FROM Transactions t_sell
        WHERE t_sell.user_id = %s 
            AND t_sell.type = 'SELL'
    ),
    UnrealizedPnl AS (
        SELECT 
            p.stock_ticker,
            (p.quantity * (s.price - p.avg_price)) AS unrealized_pnl
        FROM Portfolio p
        JOIN Stock s ON p.stock_ticker = s.ticker
        WHERE p.user_id = %s
    )
    SELECT th.*, 
        COALESCE(rp.realized_pnl, 0) AS realized_pnl, 
        COALESCE(up.unrealized_pnl, 0) AS unrealized_pnl
    FROM TransactionHistory th
    LEFT JOIN RealizedPnl rp ON th.transaction_id = rp.transaction_id
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

# In portfolio.py's get_historical_portfolio_value route
@portfolio.route("/history",methods=['GET'])
@login_required
def get_historical_portfolio_value():
    """Calculate accurate historical portfolio value"""
    user_id = current_user.user_id
    
    # Get all transactions with current prices
    query = """
    WITH all_dates AS (
        SELECT DISTINCT date_trunc('day', timestamp)::date AS date 
        FROM Transactions 
        WHERE user_id = %s
        UNION SELECT CURRENT_DATE
        ORDER BY date
    ),
    daily_holdings AS (
        SELECT 
            d.date,
            t.stock_ticker,
            SUM(CASE WHEN t.type = 'BUY' THEN t.quantity ELSE -t.quantity END) 
                OVER (PARTITION BY t.stock_ticker ORDER BY d.date) AS running_qty
        FROM all_dates d
        LEFT JOIN Transactions t ON 
            date_trunc('day', t.timestamp)::date <= d.date AND 
            t.user_id = %s
    ),
    daily_values AS (
        SELECT 
            dh.date,
            SUM(dh.running_qty * s.price) AS portfolio_value
        FROM daily_holdings dh
        JOIN Stock s ON dh.stock_ticker = s.ticker
        WHERE dh.running_qty > 0
        GROUP BY dh.date
        ORDER BY dh.date
    )
    SELECT date, portfolio_value FROM daily_values;
    """
    
    try:
        historical_data = fetch_data(query, (user_id, user_id))
        return jsonify({
            "history": [{
                "date": row["date"].strftime("%Y-%m-%d"),
                "portfolio_value": float(row["portfolio_value"])
            } for row in historical_data]
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching portfolio history: {str(e)}")
        return jsonify({"error": "Could not fetch historical data"}), 500

from decimal import Decimal

@portfolio.route("/sell-stock", methods=["POST"])
@login_required
def sell_stock():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No JSON data received"}), 400
            
        ticker = data.get('ticker', '').upper()
        quantity = Decimal(str(data.get('quantity', 0)))  # Convert to Decimal
        price = Decimal(str(data.get('price', 0)))      # Convert to Decimal
        user_id = current_user.user_id

        if quantity <= 0:
            return jsonify({"success": False, "message": "Quantity must be positive"}), 400

        # Check stock exists
        stock_data = fetch_data(
            "SELECT price FROM Stock WHERE ticker = %s;", 
            (ticker,),
            fetch_one=True
        )
        if not stock_data:
            return jsonify({"success": False, "message": "Stock not found"}), 404

        # Check user holdings - ensure we get Decimal values
        holdings = fetch_data(
            "SELECT quantity, avg_price FROM Portfolio WHERE user_id = %s AND stock_ticker = %s;",
            (user_id, ticker),
            fetch_one=True
        )
        if not holdings:
            return jsonify({"success": False, "message": f"You don't own any {ticker} shares"}), 400
        
        # Convert holdings to Decimal if they aren't already
        holdings_qty = Decimal(str(holdings["quantity"]))
        holdings_avg = Decimal(str(holdings["avg_price"]))
        
        if holdings_qty < quantity:
            return jsonify({
                "success": False, 
                "message": f"Not enough shares (You own: {holdings_qty}, Trying to sell: {quantity})"
            }), 400

        # Calculate values using Decimal
        total_value = quantity * price
        profit = quantity * (price - holdings_avg)

        # Update portfolio
        if holdings_qty == quantity:
            execute_query(
                "DELETE FROM Portfolio WHERE user_id = %s AND stock_ticker = %s;",
                (user_id, ticker)
            )
        else:
            execute_query(
                "UPDATE Portfolio SET quantity = quantity - %s WHERE user_id = %s AND stock_ticker = %s;",
                (float(quantity), user_id, ticker)  # Convert to float for PostgreSQL
            )

        # Update balance
        execute_query(
            "UPDATE Users SET balance = balance + %s WHERE user_id = %s;",
            (float(total_value), user_id)  # Convert to float for PostgreSQL
        )

        # Record transaction
        execute_query(
            "INSERT INTO Transactions (user_id, stock_ticker, type, quantity, price) VALUES (%s, %s, 'SELL', %s, %s);",
            (user_id, ticker, float(quantity), float(price))  # Convert to float for PostgreSQL
        )

        return jsonify({
            "success": True,
            "message": f"Successfully sold {quantity} shares of {ticker} for ₹{total_value:.2f}",
            "amount": str(total_value),  # Return as string to avoid JSON serialization issues
            "profit": str(profit)       # Return as string to avoid JSON serialization issues
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error selling stock: {str(e)}"
        }), 500