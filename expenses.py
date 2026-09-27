import mysql.connector
from fastmcp import FastMCP
# DB connection 

def get_connection():
    return mysql.connector.connect(
        host = "localhost",
        user = "gurnoor",
        password = "8805",
        database = "expense_tracker"
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
def list_expense():
    '''Selecting all expenses'''
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, date, amount, title, category, note FROM expenses ORDER BY id ASC'''
    )
    cols = [d for d in cursor.description]
    return [dict(zip(cols, r))for r in cursor.fetchall()]


if __name__ == "__main__":
    mcp.run()