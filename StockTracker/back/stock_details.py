from flask import Blueprint, render_template
import asyncpg
import yfinance as yf
import asyncio

DB_URL = "postgresql://neondb_owner:npg_2VY3IFQqtPlj@ep-bitter-tooth-a5v8si2g-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

stock_details = Blueprint("stock_details", __name__)

async def fetch_stock_data(ticker):
    """Fetch stock details, financials, and price history."""
    try:
        async with asyncpg.create_pool(DB_URL) as pool:
            async with pool.acquire() as conn:
                
                # ✅ Fetch stock details from the database
                stock_query = "SELECT * FROM Stock WHERE ticker = $1;"
                stock = await conn.fetchrow(stock_query, ticker)

                # ✅ Fetch yearly financials
                yearly_query = "SELECT * FROM Yearly_Financials WHERE stock_ticker = $1 ORDER BY year DESC LIMIT 1;"
                yearly_financials = await conn.fetchrow(yearly_query, ticker)

                # ✅ Fetch latest quarterly financials
                quarterly_query = "SELECT * FROM Quarterly_Financials WHERE stock_ticker = $1 ORDER BY quarter DESC LIMIT 1;"
                quarterly_financials = await conn.fetchrow(quarterly_query, ticker)

                # ✅ Fetch market analysis
                market_query = "SELECT * FROM Market_Analysis WHERE stock_ticker = $1;"
                market_analysis = await conn.fetchrow(market_query, ticker)

        # ✅ Fetch real-time stock data from Yahoo Finance
        stock_obj = yf.Ticker(ticker)
        hist = stock_obj.history(period="6mo")  # Fetch past 6 months data

        chart_data = {
            "dates": hist.index.strftime("%Y-%m-%d").tolist(),
            "prices": hist["Close"].tolist()
        }

        return {
            "stock": stock,
            "yearly_financials": yearly_financials,
            "quarterly_financials": quarterly_financials,
            "market_analysis": market_analysis,
            "chart_data": chart_data
        }

    except Exception as e:
        print(f"❌ Error fetching stock data for {ticker}: {e}")
        return None  # Return None if there's an error

@stock_details.route("/stock/<ticker>")
def stock_page(ticker):
    """Render stock details page."""
    stock_data = asyncio.run(fetch_stock_data(ticker))  # ✅ Convert async to sync
    if not stock_data or not stock_data["stock"]:
        return "Stock not found", 404  # Return 404 if stock does not exist
    return render_template("stock_details.html", **stock_data)
