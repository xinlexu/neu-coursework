"""
Lab 09: Transaction test with Python
Edit USER and PASS before running.
Run with: python3 tx_lab.py
"""
import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        database='sanjose',
        user='USER',
        password='PASS'
    )

    conn.autocommit = False
    cursor = conn.cursor()

    # Deposit to account A
    sql_update_query = """UPDATE acct SET bal = bal + 100 WHERE id = 'A'"""
    cursor.execute(sql_update_query)

    # Withdraw from account B
    sql_update_query = """UPDATE acct SET bal = bal - 100 WHERE id = 'B'"""
    # Withdraw from account B with Error
    # sql_update_query = """UPDATE acct SET bal = bal - 100 WHERE d = 'B'"""
    cursor.execute(sql_update_query)

    print("Record updated successfully")
    conn.commit()

except mysql.connector.Error as error:
    print(f"Failed to update record to database rollback: {error}")
    conn.rollback()

finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()
        print("connection is closed")
