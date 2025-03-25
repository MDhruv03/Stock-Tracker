import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
from flask_login import UserMixin

# Database connection string
DB_URL = "postgresql://neondb_owner:npg_2VY3IFQqtPlj@ep-bitter-tooth-a5v8si2g-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

def get_db_connection():
    """Establish a new database connection."""
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

# --------------------------
# ✅ User Model (Direct SQL)
# --------------------------
class User(UserMixin):
    def __init__(self, user_id, name, password_hash, brokerage_id, balance):
        self.user_id = user_id
        self.name = name
        self.password_hash = password_hash
        self.brokerage_id = brokerage_id
        self.balance = balance

    def set_password(self, password):
        """Hashes and sets the password."""
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, password):
        """Checks if a given password matches the stored hash."""
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

    def get_id(self):
        """Ensure it returns a string, required by Flask-Login."""
        return str(self.user_id)

    @staticmethod
    def fetch_user_by_name(name):
        """Fetch user from database by name."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE name = %s", (name,))
        user_data = cur.fetchone()
        cur.close()
        conn.close()
        if user_data:
            return User(**user_data)  # Convert row to User object
        return None

    @staticmethod
    def create_user(name, password, brokerage_id):
        """Create a new user with hashed password."""
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Users (name, password_hash, brokerage_id, balance) VALUES (%s, %s, %s, %s)",
            (name, hashed_password, int(brokerage_id), 10000),
        )
        conn.commit()
        cur.close()
        conn.close()

# --------------------------
# ✅ Stock Model (Direct SQL)
# --------------------------
class Stock:
    def __init__(self, ticker, name, price, high_52, low_52):
        self.ticker = ticker
        self.name = name
        self.price = price
        self.high_52 = high_52
        self.low_52 = low_52

    @staticmethod
    def fetch_all_stocks():
        """Fetch all stocks from the database."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM stock")
        stocks = cur.fetchall()
        cur.close()
        conn.close()
        return [Stock(**stock) for stock in stocks]  # Convert each row to a Stock object

# --------------------------
# ✅ Broker Model (Direct SQL)
# --------------------------
class Broker:
    def __init__(self, brokerage_id, name, user_count):
        self.brokerage_id = brokerage_id
        self.name = name
        self.user_count = user_count

    @staticmethod
    def fetch_all_brokers():
        """Fetch all brokers from the database."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM brokers")
        brokers = cur.fetchall()
        cur.close()
        conn.close()
        return [Broker(**broker) for broker in brokers]  # Convert each row to a Broker object
