import asyncpg
import asyncio
from app import app
# PostgreSQL Connection URL (Replace with your actual NeonDB credentials)
DB_URL = "postgresql://neondb_owner:npg_2VY3IFQqtPlj@ep-bitter-tooth-a5v8si2g-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

async def call_function(func_name, *args):
    """Calls a PostgreSQL function and returns the result."""
    conn = await asyncpg.connect(DB_URL)
    result = await conn.fetch(f"SELECT * FROM {func_name}({', '.join(['$' + str(i + 1) for i in range(len(args))])})", *args)
    await conn.close()
    return result

async def buy_stock(user_id, ticker, quantity, price):
    await call_function("buy_stock", user_id, ticker, quantity, price)
    print("✅ Stock purchased successfully!")

async def sell_stock(user_id, ticker, quantity, price):
    await call_function("sell_stock", user_id, ticker, quantity, price)
    print("✅ Stock sold successfully!")

async def get_high_low_stocks():
    stocks = await call_function("get_high_low_stocks")
    for stock in stocks:
        print(f"{stock['ticker']} - {stock['name']} | High: {stock['high_52']} | Low: {stock['low_52']}")

async def filter_stocks(min_eps, max_pe):
    stocks = await call_function("filter_stocks", min_eps, max_pe)
    for stock in stocks:
        print(f"{stock['ticker']} - {stock['name']} | EPS: {stock['eps']} | P/E: {stock['pe']}")




