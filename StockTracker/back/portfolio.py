from flask import Blueprint, render_template
from flask_login import login_required, current_user
import asyncpg
import asyncio

DB_URL = "postgresql://neondb_owner:npg_2VY3IFQqtPlj@ep-bitter-tooth-a5v8si2g-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

portfolio = Blueprint("portfolio", __name__)

async def fetch_portfolio(user_id):
    """Fetch portfolio details from PostgreSQL."""
    try:
        conn = await asyncpg.connect(DB_URL)
        portfolio_query = "SELECT * FROM get_user_portfolio($1);"
        user_stocks = await conn.fetch(portfolio_query, user_id)
        await conn.close()
        return user_stocks
    except Exception as e:
        print(f"❌ Error fetching portfolio: {e}")
        return []

async def fetch_available_stocks():
    """Fetch all stocks from the Stock table."""
    try:
        conn = await asyncpg.connect(DB_URL)
        query = "SELECT ticker, name, price, high_52, low_52 FROM Stock;"
        stocks = await conn.fetch(query)
        await conn.close()
        return stocks
    except Exception as e:
        print(f"❌ Error fetching stocks: {e}")
        return []

@portfolio.route("/")
@login_required
def view_portfolio():
    """Render portfolio.html with user's stock holdings."""
    user_id = current_user.user_id

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    user_stocks = loop.run_until_complete(fetch_portfolio(user_id))

    return render_template("portfolio.html", stocks=user_stocks)

@portfolio.route("/buy-stocks")
@login_required
def buy_stocks():
    """Render buy_stocks.html with available stocks."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    all_stocks = loop.run_until_complete(fetch_available_stocks())

    return render_template("buy_stocks.html", stocks=all_stocks)

# @stock_details.route("/stock/<ticker>")
# def stock_page(ticker):  
#     stock = asyncio.run(fetch_stock_details(ticker))  # ✅ Convert async to sync
#     return render_template("stock_details.html", stock=stock)
