# from flask import Flask, request, jsonify, current_app
# import psycopg2
# import time

# # Initialize Flask App
# app = Flask(__name__)

# # ✅ Function to execute SQL commands
# def execute_query(query, params=None, fetch=False, fetchone=False):
#     """Execute SQL queries using the connection pool."""
#     conn = None
#     try:
#         start_time = time.perf_counter()
#         conn = current_app.db_pool.getconn()  # Get connection from pool
#         with conn.cursor() as cur:
#             cur.execute(query, params or ())
#             if fetch:
#                 data = cur.fetchall() if not fetchone else cur.fetchone()
#                 end_time = time.perf_counter()
#                 print(f"⏳ Query executed in {end_time - start_time:.4f} seconds")
#                 return data
#             conn.commit()
#         end_time = time.perf_counter()
#         print(f"⏳ Query executed in {end_time - start_time:.4f} seconds")
#     except Exception as e:
#         print(f"❌ Database Error: {e}")
#         return None
#     finally:
#         if conn:
#             current_app.db_pool.putconn(conn)  # Return connection to pool

# # ✅ Helper function to call PostgreSQL stored procedures
# def call_function(func_name, *args):
#     """Call a stored function from PostgreSQL."""
#     placeholders = ", ".join(["%s"] * len(args))
#     return execute_query(f"SELECT * FROM {func_name}({placeholders})", args, fetch=True)

# # ✅ Buy Stock API
# @app.route("/buy", methods=["POST"])
# def buy_stock():
#     data = request.json
#     call_function("buy_stock", data["user_id"], data["ticker"], data["quantity"], data["price"], data["high_52"], data["low_52"])
#     return jsonify({"message": "Stock bought successfully!"})

# # ✅ Sell Stock API
# @app.route("/sell", methods=["POST"])
# def sell_stock():
#     data = request.json
#     call_function("sell_stock", data["user_id"], data["ticker"], data["quantity"], data["price"])
#     return jsonify({"message": "Stock sold successfully!"})

# # ✅ Get 52-Week High/Low Stocks API
# @app.route("/high_low", methods=["GET"])
# def get_high_low():
#     stocks = call_function("get_high_low_stocks")
#     return jsonify([dict(stock) for stock in stocks]) if stocks else jsonify([])

# # ✅ Filter Stocks API
# @app.route("/filter_stocks", methods=["POST"])
# def filter_stocks():
#     data = request.json
#     stocks = call_function("filter_stocks", data["min_eps"], data["max_pe"])
#     return jsonify([dict(stock) for stock in stocks]) if stocks else jsonify([])

# # ✅ Fetch Latest Stock Prices API
# @app.route("/prices", methods=["GET"])
# def get_prices():
#     """Fetch latest stock prices from the database."""
#     stocks = execute_query("SELECT ticker, price FROM Stock", fetch=True)
#     return jsonify([dict(stock) for stock in stocks]) if stocks else jsonify([])

# # Run Flask App
# if __name__ == "__main__":
#     app.run(debug=True)
