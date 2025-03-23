import asyncpg
import asyncio
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from auth import auth      # Your auth blueprint
from portfolio import portfolio  # Your portfolio blueprint
from models import User   # Use User from models.py for password checking and Flask-Login
from transactions import transactions
from stock_details import stock_details

# -------------------------------
# Initialize Flask App
# -------------------------------
app = Flask(__name__)
app.config["DATABASE_URL"] = "postgresql://neondb_owner:npg_2VY3IFQqtPlj@ep-bitter-tooth-a5v8si2g-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"
app.secret_key = "supersecretkey"

# -------------------------------
# Register Blueprints
# -------------------------------
app.register_blueprint(auth)
app.register_blueprint(portfolio, url_prefix="/portfolio")
app.register_blueprint(transactions, url_prefix="/transactions")
app.register_blueprint(stock_details, url_prefix="/stock")

# -------------------------------
# Initialize Flask-Login
# -------------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

# -------------------------------
# Async Function to Get Database Connection
# -------------------------------
async def get_db_connection():
    return await asyncpg.connect(app.config["DATABASE_URL"])

# -------------------------------
# Flask-Login: Load User using raw SQL
# -------------------------------
@login_manager.user_loader
def load_user(user_id):
    # Use an asynchronous helper to load the user, then return a User object.
    data = asyncio.run(load_user_async(user_id))
    if data:
        # Construct a User object from the raw SQL row.
        # Ensure that your User class __init__ can accept the row values in order.
        return User(data["user_id"], data["name"], data["password_hash"], data["brokerage_id"], data["balance"])
    return None

async def load_user_async(user_id):
    conn = await get_db_connection()
    user = await conn.fetchrow("SELECT * FROM Users WHERE user_id=$1", int(user_id))
    await conn.close()
    return user

# -------------------------------
# Raw SQL Code: Create Tables
# -------------------------------
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS Brokers (
    brokerage_id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    user_count INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    password_hash TEXT NOT NULL,
    brokerage_id INT REFERENCES Brokers(brokerage_id),
    balance NUMERIC(15,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Stock (
    ticker VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price NUMERIC(10,2),
    high_52 NUMERIC(10,2),
    low_52 NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS Transactions (
    transaction_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id),
    stock_ticker VARCHAR(10) REFERENCES Stock(ticker),
    type VARCHAR(10) CHECK (type IN ('BUY', 'SELL')),
    quantity INT CHECK (quantity > 0),
    price NUMERIC(10,2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Quarterly_Financials (
    stock_ticker VARCHAR(10) REFERENCES Stock(ticker),
    quarter VARCHAR(10) NOT NULL,
    eps_growth NUMERIC(5,2),
    revenue_growth NUMERIC(5,2),
    profit NUMERIC(15,2),
    earnings NUMERIC(15,2),
    PRIMARY KEY (stock_ticker, quarter)
);

CREATE TABLE IF NOT EXISTS Yearly_Financials (
    stock_ticker VARCHAR(10) REFERENCES Stock(ticker),
    year INT NOT NULL,
    eps_growth NUMERIC(5,2),
    revenue_growth NUMERIC(5,2),
    profit NUMERIC(15,2),
    earnings NUMERIC(15,2),
    PRIMARY KEY (stock_ticker, year)
);

CREATE TABLE IF NOT EXISTS Portfolio (
    user_id INT REFERENCES Users(user_id),
    stock_ticker VARCHAR(10) REFERENCES Stock(ticker),
    quantity INT CHECK (quantity >= 0),
    avg_price NUMERIC(10,2),
    PRIMARY KEY (user_id, stock_ticker)
);

CREATE TABLE IF NOT EXISTS Market_Analysis (
    stock_ticker VARCHAR(10) REFERENCES Stock(ticker),
    pe_ratio NUMERIC(10,2),
    dividend_yield NUMERIC(5,2),
    market_cap NUMERIC(15,2),
    volume BIGINT
);
"""

# -------------------------------
# Raw SQL Code: Create Stored Functions
# -------------------------------
CREATE_FUNCTIONS_SQL = """
CREATE OR REPLACE FUNCTION buy_stock(
    p_user_id INT,
    p_ticker VARCHAR,
    p_quantity INT,
    p_price NUMERIC
) RETURNS VOID AS $$
BEGIN
    INSERT INTO Transactions (user_id, stock_ticker, type, quantity, price, timestamp)
    VALUES (p_user_id, p_ticker, 'BUY', p_quantity, p_price, CURRENT_TIMESTAMP);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sell_stock(
    p_user_id INT,
    p_ticker VARCHAR,
    p_quantity INT,
    p_price NUMERIC
) RETURNS VOID AS $$
DECLARE
    existing_shares INT;
    total_earnings NUMERIC;
BEGIN
    SELECT quantity INTO existing_shares FROM Portfolio WHERE user_id = p_user_id AND stock_ticker = p_ticker;
    IF existing_shares IS NULL OR existing_shares < p_quantity THEN
        RAISE EXCEPTION 'Not enough shares to sell';
    END IF;
    total_earnings := p_quantity * p_price;
    IF existing_shares = p_quantity THEN
        DELETE FROM Portfolio WHERE user_id = p_user_id AND stock_ticker = p_ticker;
    ELSE
        UPDATE Portfolio SET quantity = quantity - p_quantity WHERE user_id = p_user_id AND stock_ticker = p_ticker;
    END IF;
    UPDATE Users SET balance = balance + total_earnings WHERE user_id = p_user_id;
    INSERT INTO Transactions (user_id, stock_ticker, type, quantity, price, timestamp)
    VALUES (p_user_id, p_ticker, 'SELL', p_quantity, p_price, CURRENT_TIMESTAMP);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_high_low_stocks()
RETURNS TABLE (ticker VARCHAR, name VARCHAR, high_52 NUMERIC, low_52 NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT ticker, name, high_52, low_52 FROM Stock ORDER BY high_52 DESC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION filter_stocks(
    min_eps NUMERIC,
    max_pe NUMERIC
) RETURNS TABLE (ticker VARCHAR, name VARCHAR, eps NUMERIC, pe NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT s.ticker, s.name, yf.eps_growth, ma.pe_ratio
    FROM Stock s
    JOIN Yearly_Financials yf ON s.ticker = yf.stock_ticker
    JOIN Market_Analysis ma ON s.ticker = ma.stock_ticker
    WHERE yf.eps_growth >= min_eps AND ma.pe_ratio <= max_pe;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_user_portfolio(p_user_id INT)
RETURNS TABLE (
    stock_ticker VARCHAR(15),
    stock_name VARCHAR(255),
    quantity INT,
    avg_price NUMERIC(10,2),
    current_price NUMERIC(10,2),
    total_investment NUMERIC(15,2),
    current_value NUMERIC(15,2),
    profit_loss NUMERIC(15,2),
    profit_loss_pct NUMERIC(6,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.stock_ticker,
        s.name AS stock_name,
        p.quantity,
        p.avg_price,
        s.price AS current_price,
        (p.quantity * p.avg_price) AS total_investment,
        (p.quantity * s.price) AS current_value,
        (p.quantity * s.price) - (p.quantity * p.avg_price) AS profit_loss,
        CASE 
            WHEN (p.quantity * p.avg_price) = 0 THEN 0
            ELSE ROUND((((p.quantity * s.price) - (p.quantity * p.avg_price)) / (p.quantity * p.avg_price)) * 100, 2)
        END AS profit_loss_pct
    FROM Portfolio p
    JOIN Stock s ON p.stock_ticker = s.ticker
    WHERE p.user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;
"""

# -------------------------------
# Asynchronous Initialization: Create Tables & Stored Functions
# -------------------------------
async def initialize_database():
    """Creates tables and stored functions in PostgreSQL."""
    try:
        conn = await get_db_connection()
        await conn.execute(CREATE_TABLES_SQL)
        print("✅ Tables created successfully!")
        await conn.execute(CREATE_FUNCTIONS_SQL)
        print("✅ Functions created successfully!")
        await conn.close()
    except Exception as e:
        print(f"❌ Database Initialization Failed: {e}")

# -------------------------------
# Run Flask App and Initialize DB
# -------------------------------
if __name__ == "__main__":
    asyncio.run(initialize_database())
    app.run(debug=True)
