from flask import Blueprint, request, redirect, url_for, flash
from flask_login import login_required, current_user
import asyncpg
import asyncio

# PostgreSQL Connection URL
DB_URL = "postgresql://neondb_owner:npg_2VY3IFQqtPlj@ep-bitter-tooth-a5v8si2g-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

transactions = Blueprint("transactions", __name__)

async def execute_query(query, *args):
    """Helper function to execute SQL queries asynchronously"""
    conn = await asyncpg.connect(DB_URL)
    await conn.execute(query, *args)
    await conn.close()

async def fetch_one(query, *args):
    """Helper function to fetch a single row asynchronously"""
    conn = await asyncpg.connect(DB_URL)
    result = await conn.fetchrow(query, *args)
    await conn.close()
    return result

async def fetch_all(query, *args):
    """Helper function to fetch multiple rows asynchronously"""
    conn = await asyncpg.connect(DB_URL)
    result = await conn.fetch(query, *args)
    await conn.close()
    return result

@transactions.route("/buy", methods=["POST"])
@login_required
def buy_stock():
    ticker = request.form["ticker"].upper()
    quantity = int(request.form["quantity"])

    async def process_buy():
        # ✅ Fetch stock price
        stock_data = await fetch_one("SELECT price FROM Stock WHERE ticker = $1", ticker)
        if not stock_data:
            flash("Stock not found")
            return redirect(url_for("portfolio.view_portfolio"))
        
        stock_price = stock_data["price"]
        total_cost = quantity * stock_price

        # ✅ Fetch user balance
        user_balance_data = await fetch_one("SELECT balance FROM Users WHERE user_id = $1", current_user.user_id)
        if not user_balance_data or user_balance_data["balance"] < total_cost:
            flash("Insufficient balance")
            return redirect(url_for("portfolio.view_portfolio"))

        # ✅ Deduct balance from user
        await execute_query("UPDATE Users SET balance = balance - $1 WHERE user_id = $2", total_cost, current_user.user_id)

        # ✅ Check if user already owns this stock
        portfolio_entry = await fetch_one(
            "SELECT quantity, avg_price FROM Portfolio WHERE user_id = $1 AND stock_ticker = $2", 
            current_user.user_id, ticker
        )

        if portfolio_entry:
            old_quantity = portfolio_entry["quantity"]
            old_avg_price = portfolio_entry["avg_price"]
            new_avg_price = ((old_avg_price * old_quantity) + total_cost) / (old_quantity + quantity)

            # ✅ Update Portfolio
            await execute_query(
                "UPDATE Portfolio SET quantity = quantity + $1, avg_price = $2 WHERE user_id = $3 AND stock_ticker = $4",
                quantity, new_avg_price, current_user.user_id, ticker
            )
        else:
            # ✅ Insert new stock into Portfolio
            await execute_query(
                "INSERT INTO Portfolio (user_id, stock_ticker, quantity, avg_price) VALUES ($1, $2, $3, $4)",
                current_user.user_id, ticker, quantity, stock_price
            )

        # ✅ Insert Transaction
        await execute_query(
            "INSERT INTO Transactions (user_id, stock_ticker, type, quantity, price) VALUES ($1, $2, 'BUY', $3, $4)",
            current_user.user_id, ticker, quantity, stock_price
        )

        flash(f"Successfully bought {quantity} shares of {ticker}")

    asyncio.run(process_buy())
    return redirect(url_for("portfolio.view_portfolio"))

@transactions.route("/sell", methods=["POST"])
@login_required
def sell_stock():
    ticker = request.form["ticker"].upper()
    quantity = int(request.form["quantity"])

    async def process_sell():
        # ✅ Fetch stock price
        stock_data = await fetch_one("SELECT price FROM Stock WHERE ticker = $1", ticker)
        if not stock_data:
            flash("Stock not found")
            return redirect(url_for("portfolio.view_portfolio"))

        stock_price = stock_data["price"]
        total_earnings = quantity * stock_price

        # ✅ Check if user owns enough shares
        portfolio_entry = await fetch_one(
            "SELECT quantity FROM Portfolio WHERE user_id = $1 AND stock_ticker = $2", 
            current_user.user_id, ticker
        )

        if not portfolio_entry or portfolio_entry["quantity"] < quantity:
            flash("Not enough shares to sell")
            return redirect(url_for("portfolio.view_portfolio"))

        # ✅ Update Portfolio
        if portfolio_entry["quantity"] == quantity:
            await execute_query("DELETE FROM Portfolio WHERE user_id = $1 AND stock_ticker = $2", current_user.user_id, ticker)
        else:
            await execute_query(
                "UPDATE Portfolio SET quantity = quantity - $1 WHERE user_id = $2 AND stock_ticker = $3",
                quantity, current_user.user_id, ticker
            )

        # ✅ Update User Balance
        await execute_query("UPDATE Users SET balance = balance + $1 WHERE user_id = $2", total_earnings, current_user.user_id)

        # ✅ Insert Transaction
        await execute_query(
            "INSERT INTO Transactions (user_id, stock_ticker, type, quantity, price) VALUES ($1, $2, 'SELL', $3, $4)",
            current_user.user_id, ticker, quantity, stock_price
        )

        flash(f"Successfully sold {quantity} shares of {ticker}")

    asyncio.run(process_sell())
    return redirect(url_for("portfolio.view_portfolio"))
