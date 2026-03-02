import aiosqlite

DB_PATH = "homework.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS homework (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                task TEXT NOT NULL,
                date TEXT NOT NULL
            )
        """)
        await db.commit()

async def add_homework(subject: str, task: str, date: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO homework (subject, task, date) VALUES (?, ?, ?)",
            (subject, task, date)
        )
        await db.commit()

async def get_homework(date: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT subject, task FROM homework WHERE date = ? ORDER BY subject",
            (date,)
        ) as cursor:
            return await cursor.fetchall()

async def delete_homework(subject: str, date: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM homework WHERE subject = ? AND date = ?",
            (subject, date)
        )
        await db.commit()