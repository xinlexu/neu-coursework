import mysql.connector

conn = None
cursor = None

try:
    conn = mysql.connector.connect(
        host='127.0.0.1',
        port=3306,
        database='sanjose',
        user='lab9user',
        password='Lab9Pass_123!'
    )

    conn.autocommit = False
    cursor = conn.cursor()

    cursor.execute("UPDATE ACCT SET BAL = BAL + 100 WHERE ID = 'A'")
    cursor.execute("UPDATE ACCT SET BAL = BAL - 100 WHERE ID = 'B'")

    conn.commit()
    print("Record updated successfully")

except mysql.connector.Error as error:
    print(f"Failed to update record to database rollback: {error}")
    if conn is not None and conn.is_connected():
        conn.rollback()

finally:
    if cursor is not None:
        cursor.close()
    if conn is not None and conn.is_connected():
        conn.close()
    print("connection is closed")
