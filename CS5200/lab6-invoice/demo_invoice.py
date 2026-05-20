import mysql.connector
import os

conn = mysql.connector.connect(
    host="localhost",
    user=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", ""),
    database="demo_db"
)

cursor = conn.cursor()

order_id = input("Enter Order ID: ")

query = """
SELECT c.name, c.zip,
       o.order_date,
       p.name, oi.quantity, p.price
FROM orders o
JOIN customer c ON o.customer_id = c.id
JOIN order_item oi ON o.order_id = oi.order_id
JOIN product p ON oi.product_id = p.product_id
WHERE o.order_id = %s
"""

cursor.execute(query, (order_id,))
rows = cursor.fetchall()

total = 0

print("\n===== SIMPLE INVOICE =====")

for row in rows:
    name, zip_code, date, product, qty, price = row
    amount = qty * price
    total += amount
    print(f"{name} | {product} | {qty} x {price} = {amount}")

print(f"TOTAL: {total}")

cursor.close()
conn.close()
