import aiosqlite

DB_PATH = "homework.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS homework (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                date TEXT NOT NULL UNIQUE
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY
            )
        """)
        await db.commit()

async def add_homework(task: str, date: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO homework (task, date) VALUES (?, ?)",
            (task, date)
        )
        await db.commit()

async def get_homework(date: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT task FROM homework WHERE date = ?", (date,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def clear_homework(date: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM homework WHERE date = ?", (date,))
        await db.commit()

async def add_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,)
        )
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            return await cursor.fetchall()
