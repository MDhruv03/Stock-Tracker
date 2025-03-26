from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required

buy_stocks = Blueprint("buy_stocks", __name__)

def fetch_data(query, params=None):
    """ Fetch data from PostgreSQL using connection pooling. """
    conn = current_app.config["DB_POOL"].getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            column_names = [desc[0] for desc in cur.description]
            return [dict(zip(column_names, row)) for row in cur.fetchall()]
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return []
    finally:
        current_app.config["DB_POOL"].putconn(conn)

@buy_stocks.route("/buy-stocks")
@login_required
def buy_stocks_page():
    """Fetch available stocks and render the buy stocks page."""
    query = "SELECT ticker, name, price, high_52, low_52 FROM Stock;"
    stocks = fetch_data(query)
    return render_template("buy_stocks.html", stocks=stocks)

@buy_stocks.route("/high-stocks", methods=["GET"])
def high_stocks():
    """ Fetch and return stocks where 52W high is at least 2.1x the low. """
    query = "SELECT * FROM get_high_stocks();"
    stocks = fetch_data(query)
    return jsonify(stocks)

@buy_stocks.route("/low-stocks", methods=["GET"])
def low_stocks():
    """ Fetch and return stocks where 52W low has not changed. """
    query = "SELECT * FROM get_low_stocks();"
    stocks = fetch_data(query)
    return jsonify(stocks)

@buy_stocks.route("/filter-stocks", methods=["POST"])
def filter_stocks():
    """ Filter stocks based on user-provided criteria. """
    data = request.json
    min_eps = data.get("min_eps", 0)
    max_pe = data.get("max_pe", 100)

    query = "SELECT * FROM filter_stocks(%s, %s);"
    stocks = fetch_data(query, (min_eps, max_pe))

    return jsonify(stocks)
