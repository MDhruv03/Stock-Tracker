import asyncpg
import asyncio
import yfinance as yf

DB_URL = "postgresql://neondb_owner:npg_2VY3IFQqtPlj@ep-bitter-tooth-a5v8si2g-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

async def update_stock_prices():
    conn = await asyncpg.connect(DB_URL)

    # Fetch tickers from the stock table
    rows = await conn.fetch("SELECT ticker FROM stock")
    tickers = [row["ticker"] for row in rows]

    if not tickers:
        print("No stocks found.")
        await conn.close()
        return

    print(f"Fetching prices and financials for: {tickers}")

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            
            # Fetch real-time stock data
            stock_data = stock.history(period="1d")
            if stock_data.empty:
                print(f"⚠️ No data found for {ticker}. Skipping update.")
                continue
            
            latest_price = float(stock_data["Close"].iloc[-1])
            high_52 = float(stock.info.get("fiftyTwoWeekHigh", 0))
            low_52 = float(stock.info.get("fiftyTwoWeekLow", 0))
            stock_name = stock.info.get("longName", "Unknown")

            print(f"✅ {ticker} Price: {latest_price}, 52W High: {high_52}, 52W Low: {low_52}")

            # Update Stock Table
            await conn.execute(
                """INSERT INTO stock (ticker, name, price, high_52, low_52)
                   VALUES ($1, $2, $3, $4, $5)
                   ON CONFLICT (ticker) 
                   DO UPDATE SET 
                       name = EXCLUDED.name,
                       price = EXCLUDED.price, 
                       high_52 = EXCLUDED.high_52, 
                       low_52 = EXCLUDED.low_52""",
                ticker, stock_name, latest_price, high_52, low_52
            )

            # Fetch and update Market Analysis Table
            pe_ratio = float(stock.info.get("trailingPE", 0))
            dividend_yield = float(stock.info.get("dividendYield", 0) or 0) * 100
            market_cap = round(float(stock.info.get("marketCap", 0)) / 1e6, 2)
            volume = int(stock_data["Volume"].iloc[-1])

            print(f"📊 {ticker} P/E: {pe_ratio}, Div Yield: {dividend_yield}%, Market Cap: {market_cap}M, Volume: {volume}")

            await conn.execute(
                """INSERT INTO market_analysis (stock_ticker, pe_ratio, dividend_yield, market_cap, volume)
                   VALUES ($1, $2, $3, $4, $5)
                   ON CONFLICT (stock_ticker) 
                   DO UPDATE SET 
                       pe_ratio = EXCLUDED.pe_ratio,
                       dividend_yield = EXCLUDED.dividend_yield,
                       market_cap = EXCLUDED.market_cap,
                       volume = EXCLUDED.volume""",
                ticker, pe_ratio, dividend_yield, market_cap, volume
            )

            # Fetch and update Yearly Financials Table
            eps_growth = float(stock.info.get("earningsGrowth", 0))
            revenue_growth = float(stock.info.get("revenueGrowth", 0))
            profit = round(float(stock.info.get("netIncomeToCommon", 0)) / 1e6, 2)
            earnings = round(float(stock.info.get("totalRevenue", 0)) / 1e6, 2)
            year = 2024  

            print(f"📈 {ticker} EPS Growth: {eps_growth}, Revenue Growth: {revenue_growth}, Profit: {profit}M, Earnings: {earnings}M")

            await conn.execute(
                """INSERT INTO yearly_financials (stock_ticker, year, eps_growth, revenue_growth, profit, earnings)
                   VALUES ($1, $2, $3, $4, $5, $6)
                   ON CONFLICT (stock_ticker, year) 
                   DO UPDATE SET 
                       eps_growth = EXCLUDED.eps_growth,
                       revenue_growth = EXCLUDED.revenue_growth,
                       profit = EXCLUDED.profit,
                       earnings = EXCLUDED.earnings""",
                ticker, year, eps_growth, revenue_growth, profit, earnings
            )

            # Fetch and update Quarterly Financials Table
            quarterly_financials = None  # Initialize to prevent UnboundLocalError
            try:
                quarterly_financials = stock.quarterly_financials
                if quarterly_financials is not None and not quarterly_financials.empty:
                    latest_quarter = str(quarterly_financials.columns[0].date())  

                    eps_growth_q = round(float(quarterly_financials.loc["Diluted EPS", latest_quarter]), 2) if "Diluted EPS" in quarterly_financials.index else 0
                    revenue_growth_q = round(float(quarterly_financials.loc["Total Revenue", latest_quarter]) / 1e6, 2) if "Total Revenue" in quarterly_financials.index else 0
                    profit_q = round(float(quarterly_financials.loc["Net Income", latest_quarter]) / 1e6, 2) if "Net Income" in quarterly_financials.index else 0
                    earnings_q = round(float(quarterly_financials.loc["Gross Profit", latest_quarter]) / 1e6, 2) if "Gross Profit" in quarterly_financials.index else 0

                    print(f"📊 {ticker} Quarterly Financials ({latest_quarter}): EPS {eps_growth_q}, Revenue Growth {revenue_growth_q}M, Profit {profit_q}M, Earnings {earnings_q}M")

                    await conn.execute(
                        """INSERT INTO quarterly_financials (stock_ticker, quarter, eps_growth, revenue_growth, profit, earnings)
                           VALUES ($1, $2, $3, $4, $5, $6)
                           ON CONFLICT (stock_ticker, quarter) 
                           DO UPDATE SET 
                               eps_growth = EXCLUDED.eps_growth,
                               revenue_growth = EXCLUDED.revenue_growth,
                               profit = EXCLUDED.profit,
                               earnings = EXCLUDED.earnings""",
                        ticker, latest_quarter, eps_growth_q, revenue_growth_q, profit_q, earnings_q
                    )
                else:
                    print(f"⚠️ {ticker} has no quarterly financial data.")
            except Exception as e:
                print(f"⚠️ Could not fetch quarterly financials for {ticker}: {e}")

        except Exception as e:
            print(f"❌ Error updating {ticker}: {e}")

    print("✅ All stock data updated successfully!")
    await conn.close()

asyncio.run(update_stock_prices())
