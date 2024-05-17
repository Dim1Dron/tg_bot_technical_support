import aiosqlite


class Database:
    def __init__(self, db_path):
        self.db_path = db_path

    async def execute(self, query, *params):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, params)
            await db.commit()

    async def fetchone(self, query, *params):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, params)
            result = await cursor.fetchone()
            await cursor.close()
            return result

    async def fetchall(self, query, *params):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, params)
            result = await cursor.fetchall()
            await cursor.close()
            return result

db = Database('database.db')
