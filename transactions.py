from flask import Blueprint, request, redirect, url_for, flash, current_app,jsonify
from flask_login import login_required, current_user

transactions = Blueprint("transactions", __name__)

def fetch_data(query, params=()):
    """Fetch data using Flask connection pool."""
    conn = current_app.config["DB_POOL"].getconn()
    cur = conn.cursor()
    cur.execute(query, params)
    result = cur.fetchall()  # Always returns a list of tuples
    cur.close()
    current_app.config["DB_POOL"].putconn(conn)
    return result

def execute_query(query, params=()):
    """Executes a query using Flask connection pool."""
    conn = current_app.config["DB_POOL"].getconn()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    cur.close()
    current_app.config["DB_POOL"].putconn(conn)

@transactions.route("/buy", methods=["POST"])
@login_required
def buy_stock():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No JSON data received"}), 400
            
        ticker = data.get('ticker', '').upper()
        quantity = int(data.get('quantity', 0))
        price = float(data.get('price', 0))
        user_id = current_user.user_id

        if quantity <= 0:
            return jsonify({"success": False, "message": "Quantity must be positive"}), 400

        # Check stock exists
        stock_data = fetch_data(
            "SELECT price FROM Stock WHERE ticker = %s;", 
            (ticker,)
        )
        if not stock_data:
            return jsonify({"success": False, "message": "Stock not found"}), 404

        total_cost = quantity * price

        # Check user balance
        user_balance = fetch_data(
            "SELECT balance FROM Users WHERE user_id = %s;",
            (user_id,)
        )
        if not user_balance or user_balance[0][0] < total_cost:
            return jsonify({
                "success": False, 
                "message": f"Insufficient balance (Needed: ₹{total_cost:.2f})"
            }), 400

        # Deduct balance
        execute_query(
            "UPDATE Users SET balance = balance - %s WHERE user_id = %s;",
            (total_cost, user_id)
        )

        # Record transaction
        execute_query(
            "INSERT INTO Transactions (user_id, stock_ticker, type, quantity, price) VALUES (%s, %s, 'BUY', %s, %s);",
            (user_id, ticker, quantity, price)
        )

        # Update portfolio
        portfolio_data = fetch_data(
            "SELECT quantity, avg_price FROM Portfolio WHERE user_id = %s AND stock_ticker = %s;",
            (user_id, ticker)
        )

        if portfolio_data:
            old_qty = portfolio_data[0][0]
            old_avg = portfolio_data[0][1]
            new_qty = old_qty + quantity
            new_avg = ((old_qty * old_avg) + (quantity * price)) / new_qty
            
            execute_query(
                "UPDATE Portfolio SET quantity = %s, avg_price = %s WHERE user_id = %s AND stock_ticker = %s;",
                (new_qty, new_avg, user_id, ticker)
            )
        else:
            execute_query(
                "INSERT INTO Portfolio (user_id, stock_ticker, quantity, avg_price) VALUES (%s, %s, %s, %s);",
                (user_id, ticker, quantity, price)
            )

        return jsonify({
            "success": True,
            "message": f"Successfully bought {quantity} shares of {ticker} for ₹{total_cost:.2f}",
            "amount": str(total_cost)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error buying stock: {str(e)}"
        }), 500