import psycopg2
from psycopg2.extras import RealDictCursor

# PostgreSQL Connection URL (Replace with your actual NeonDB credentials)
DB_URL = "postgresql://neondb_owner:npg_2VY3IFQqtPlj@ep-bitter-tooth-a5v8si2g-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

def get_db_connection():
    """Establish a new database connection."""
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

def call_function(func_name, *args):
    """Calls a PostgreSQL function and returns the result."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {func_name}({', '.join(['%s' for _ in args])})", args)
    result = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return result

def buy_stock(user_id, ticker, quantity, price):
    """Executes the buy_stock function in PostgreSQL."""
    call_function("buy_stock", user_id, ticker, quantity, price)
    print("✅ Stock purchased successfully!")

def sell_stock(user_id, ticker, quantity, price):
    """Executes the sell_stock function in PostgreSQL."""
    call_function("sell_stock", user_id, ticker, quantity, price)
    print("✅ Stock sold successfully!")

def get_high_low_stocks():
    """Fetches stocks with their 52-week high & low values."""
    stocks = call_function("get_high_low_stocks")
    for stock in stocks:
        print(f"{stock['ticker']} - {stock['name']} | High: {stock['high_52']} | Low: {stock['low_52']}")

def filter_stocks(min_eps, max_pe):
    """Filters stocks based on EPS and P/E ratio."""
    stocks = call_function("filter_stocks", min_eps, max_pe)
    for stock in stocks:
        print(f"{stock['ticker']} - {stock['name']} | EPS: {stock['eps']} | P/E: {stock['pe']}")
