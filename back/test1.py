import psycopg2
from flask import Flask, current_app
from psycopg2 import pool
import urllib.parse as urlparse

# Flask app setup
app = Flask(__name__)

# Your PostgreSQL connection string
DATABASE_URL = "postgresql://neondb_owner:npg_2VY3IFQqtPlj@ep-bitter-tooth-a5v8si2g-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

# Parse the connection string
url = urlparse.urlparse(DATABASE_URL)

# Set up connection pooling using psycopg2
app.config["DB_POOL"] = psycopg2.pool.SimpleConnectionPool(
    1, 20,  # Min and Max connections
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port,
    database=url.path[1:],  # Strip the 'postgres://' prefix
    sslmode='require'
)

def fetch_data(query, params=None, fetch_one=False):
    """ Fetch data from PostgreSQL using connection pooling. """
    conn = current_app.config["DB_POOL"].getconn()  # Get connection from the pool
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())  # Execute the query with params if provided
            column_names = [desc[0] for desc in cur.description]  # Get column names

            if fetch_one:
                row = cur.fetchone()
                return dict(zip(column_names, row)) if row else None
            else:
                rows = cur.fetchall()
                return [dict(zip(column_names, row)) for row in rows]  # Convert to list of dicts
    finally:
        current_app.config["DB_POOL"].putconn(conn)  # Return the connection to the pool


# Wrap the execution in app context
if __name__ == "__main__":
    with app.app_context():  # Create application context
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
                    t.stock_ticker,
                    SUM(
                        CASE 
                            WHEN t.type = 'SELL' THEN (t.quantity * (t.price - p.avg_price))
                            ELSE 0 
                        END
                    ) AS realized_pnl
                FROM Transactions t
                JOIN Portfolio p ON t.stock_ticker = p.stock_ticker AND t.user_id = p.user_id
                WHERE t.user_id = %s
                GROUP BY t.stock_ticker
            ),
            UnrealizedPnl AS (
                SELECT 
                    p.stock_ticker,
                    (p.quantity * (s.price - p.avg_price)) AS unrealized_pnl
                FROM Portfolio p
                JOIN Stock s ON p.stock_ticker = s.ticker
                WHERE p.user_id = %s
            )
            SELECT th.*, rp.realized_pnl, up.unrealized_pnl
            FROM TransactionHistory th
            LEFT JOIN RealizedPnl rp ON th.stock_ticker = rp.stock_ticker
            LEFT JOIN UnrealizedPnl up ON th.stock_ticker = up.stock_ticker;
        """
        
        user_id = 1  # Use a valid user ID for testing
        data = fetch_data(query, (user_id, user_id, user_id))  # Pass user_id three times

        # Print out the result to see the output
        if data:
            print("Query Results:")
            for row in data:
                print(row)
        else:
            print("No data found for the given user_id.")
