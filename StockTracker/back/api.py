from flask import Flask, request, jsonify
import asyncio
import asyncpg

# Initialize Flask App
app = Flask(__name__)

# Database Connection
DB_URL = "postgresql://neondb_owner:npg_2VY3IFQqtPlj@ep-bitter-tooth-a5v8si2g-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

# Helper function to call PostgreSQL stored procedures
async def call_function(func_name, *args):
    conn = await asyncpg.connect(DB_URL)
    result = await conn.fetch(f"SELECT * FROM {func_name}({', '.join(['$' + str(i+1) for i in range(len(args))])})", *args)
    await conn.close()
    return result

# ✅ Buy Stock API
@app.route("/buy", methods=["POST"])
def buy_stock():
    data = request.json
    async def run():
        await call_function("buy_stock", data["user_id"], data["ticker"], data["quantity"], data["price"], data["high_52"], data["low_52"])
    asyncio.run(run())
    return jsonify({"message": "Stock bought successfully!"})

# ✅ Sell Stock API
@app.route("/sell", methods=["POST"])
def sell_stock():
    data = request.json
    async def run():
        await call_function("sell_stock", data["user_id"], data["ticker"], data["quantity"], data["price"])
    asyncio.run(run())
    return jsonify({"message": "Stock sold successfully!"})

# ✅ Get 52-Week High/Low Stocks API
@app.route("/high_low", methods=["GET"])
def get_high_low():
    async def run():
        stocks = await call_function("get_high_low_stocks")
        return jsonify([dict(stock) for stock in stocks])
    return asyncio.run(run())

# ✅ Filter Stocks API
@app.route("/filter_stocks", methods=["POST"])
def filter_stocks():
    data = request.json
    async def run():
        stocks = await call_function("filter_stocks", data["min_eps"], data["max_pe"])
        return jsonify([dict(stock) for stock in stocks])
    return asyncio.run(run())

@app.route("/prices", methods=["GET"])
async def get_prices():
    """Fetch latest stock prices from the database."""
    conn = await asyncpg.connect(DB_URL)
    stocks = await conn.fetch("SELECT ticker, price FROM Stock")
    await conn.close()
    return jsonify([dict(stock) for stock in stocks])


# Run Flask App
if __name__ == "__main__":
    app.run(debug=True)
