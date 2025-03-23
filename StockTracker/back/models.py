import asyncpg
import asyncio
import bcrypt
from flask_login import UserMixin

# Database connection string
DB_URL = "postgresql://neondb_owner:npg_2VY3IFQqtPlj@ep-bitter-tooth-a5v8si2g-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

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
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, password):
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

    def get_id(self):
        return str(self.user_id)  # 🔹 Ensure it returns a string

    @staticmethod
    async def fetch_user_by_name(name):
        conn = await asyncpg.connect(DB_URL)
        user_data = await conn.fetchrow("SELECT * FROM users WHERE name = $1", name)
        await conn.close()
        if user_data:
            return User(**user_data)  # Convert row to User object
        return None
    
    @staticmethod
    async def create_user(name, password, brokerage_id):
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        conn = await asyncpg.connect(DB_URL)
        await conn.execute(
            "INSERT INTO Users (name, password_hash, brokerage_id, balance) VALUES ($1, $2, $3, $4)",
            name, hashed_password, int(brokerage_id), 10000
        )
        await conn.close()

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
    async def fetch_all_stocks():
        conn = await asyncpg.connect(DB_URL)
        stocks = await conn.fetch("SELECT * FROM stock")
        await conn.close()
        return [Stock(**dict(stock)) for stock in stocks]  # Convert each row to a Stock object

# --------------------------
# ✅ Broker Model (Direct SQL)
# --------------------------
class Broker:
    def __init__(self, brokerage_id, name, user_count):
        self.brokerage_id = brokerage_id
        self.name = name
        self.user_count = user_count

    @staticmethod
    async def fetch_all_brokers():
        conn = await asyncpg.connect(DB_URL)
        brokers = await conn.fetch("SELECT * FROM brokers")
        await conn.close()
        return [Broker(**dict(broker)) for broker in brokers]  # Convert each row to a Broker object
