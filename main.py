import os
import aiomysql
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

# DB connection pool (created once, reused across calls)
pool = None

async def get_pool():
    global pool
    if pool is None:
        pool = await aiomysql.create_pool(
            host=os.environ.get("EXPENSE_DB_HOST", "localhost"),
            user=os.environ.get("EXPENSE_DB_USER", "gurnoor"),
            password=os.environ["EXPENSE_DB_PASSWORD"],
            db=os.environ.get("EXPENSE_DB_NAME", "expense_tracker"),
            autocommit=False,
        )
    return pool


# Create MCP Server
mcp = FastMCP("expense_tracker")


@mcp.tool()
async def add_expense(date, amount: float, category: str, note: str = "", title: str = ""):
    """ADD A NEW EXPENSE ENTRY TO THE DATABASE."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO expenses (title, date, category, amount, note) VALUES (%s, %s, %s, %s, %s)",
                (title, date, category, amount, note)
            )
            await conn.commit()

    return f"Added expense '{title}' of ₹{amount} in category '{category}'."


@mcp.tool()
async def list_expense(start_date=None, end_date=None):
    """Selecting all expenses"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            if start_date and end_date:
                await cursor.execute(
                    '''SELECT id, date, amount, title, category, note FROM expenses
                       WHERE date BETWEEN %s AND %s ORDER BY id ASC''',
                    (start_date, end_date)
                )
            else:
                await cursor.execute(
                    '''SELECT id, date, amount, title, category, note FROM expenses
                       ORDER BY id ASC'''
                )

            cols = [d[0] for d in cursor.description]
            rows = await cursor.fetchall()
            result = [dict(zip(cols, r)) for r in rows]

    return result


@mcp.tool()
async def delete_expense(category: str = None, id: int = None):
    """Delete expenses"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            if id is not None:
                await cursor.execute("DELETE FROM expenses WHERE id = %s", (id,))
            elif category:
                await cursor.execute("DELETE FROM expenses WHERE category = %s", (category,))
            else:
                return "No id or category provided — nothing deleted."

            deleted = cursor.rowcount
            await conn.commit()

    if deleted == 0:
        return f"No expenses found matching the given filter."
    return f"Deleted {deleted} expense(s)."


@mcp.tool()
async def summary(st_date, end_date, category=None):
    """Summarize expenses by category within an inclusive date range"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = '''
                SELECT category, SUM(amount) AS total_amount FROM expenses
                WHERE date BETWEEN %s AND %s
            '''
            params = [st_date, end_date]

            if category:
                query += " AND category = %s"
                params.append(category)

            query += " GROUP BY category ORDER BY category ASC"

            await cursor.execute(query, params)
            cols = [d[0] for d in cursor.description]
            rows = await cursor.fetchall()
            result = [dict(zip(cols, r)) for r in rows]

    return result


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)