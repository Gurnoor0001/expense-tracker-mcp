import os
import mysql.connector
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

# DB connection 

def get_connection():
    return mysql.connector.connect(
        host = os.environ.get("EXPENSE_DB_HOST", "localhost"),
        user = os.environ.get("EXPENSE_DB_USER", "gurnoor"),
        password = os.environ["EXPENSE_DB_PASSWORD"],
        database = os.environ.get("EXPENSE_DB_NAME", "expense_tracker")
    )


# Create MCP Server 

mcp = FastMCP("expense_tracker")

@mcp.tool()
def add_expense(date, amount:float, category:str, note:str="",title: str=""):
    '''ADD A NEW EXPENSE ENTERY TO THE DATABASE.'''
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''Insert INTO expenses (title, date, category, amount,note) Value (%s,%s,%s,%s,%s)''', (title, date, category, amount, note)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return f"Added expense '{title}' of ₹{amount} in category '{category}'."
@mcp.tool()
def list_expense(start_date=None, end_date=None):
    """Selecting all expenses"""
    conn = get_connection()
    cursor = conn.cursor()

    if start_date and end_date:
        cursor.execute(
            '''SELECT id, date, amount, title, category, note FROM expenses
               WHERE date BETWEEN %s AND %s ORDER BY id ASC''',
            (start_date, end_date)
        )
    else:
        cursor.execute(
            '''SELECT id, date, amount, title, category, note FROM expenses
               ORDER BY id ASC'''
        )

    cols = [d[0] for d in cursor.description]
    result = [dict(zip(cols, r)) for r in cursor.fetchall()]

    cursor.close()
    conn.close()
    return result


@mcp.tool()
def delete_expense(category:str= None, id:int=None):
    """Delete expenses"""
    conn = get_connection()
    cursor = conn.cursor()
    if category:
        cursor.execute(
            "DELETE FROM expenses WHERE category = %s",
            (category,)
    )

    if id :
        cursor.execute(
            "DELETE FROM expenses WHERE id = %s",
            (id,)
        )
    if cursor.rowcount == 0:
        cursor.close()
        conn.close()
        return f"No expenses found with category {category}"

    conn.commit()
    cursor.close()
    conn.close()
    return f"Deleted {cursor.rowcount} expense(s) in category '{category}'."


@mcp.tool()
def summary(st_date, end_date, category=None):
    """Summarize expenses by category within an inclusive date range"""
    conn = get_connection()
    cursor = conn.cursor()

    query = '''
        SELECT category, SUM(amount) AS total_amount FROM expenses
        WHERE date BETWEEN %s AND %s
    '''
    params = [st_date, end_date]

    if category:
        query += " AND category = %s"
        params.append(category)

    query += " GROUP BY category ORDER BY category ASC"

    cursor.execute(query, params)
    cols = [d[0] for d in cursor.description]
    result = [dict(zip(cols, r)) for r in cursor.fetchall()]

    cursor.close()
    conn.close()
    return result

    
    
if __name__ == "__main__":
    mcp.run(transport="http", host = "0.0.0.0", port = 8000)