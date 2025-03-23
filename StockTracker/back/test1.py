import asyncpg
import asyncio

DB_URL = "postgresql://neondb_owner:npg_2VY3IFQqtPlj@ep-bitter-tooth-a5v8si2g-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

async def fetch_brokers():
    conn = await asyncpg.connect(DB_URL)
    brokers = await conn.fetch("SELECT * FROM Brokers")
    await conn.close()
    return [dict(broker) for broker in brokers]

brokers = asyncio.run(fetch_brokers())
print(brokers)
