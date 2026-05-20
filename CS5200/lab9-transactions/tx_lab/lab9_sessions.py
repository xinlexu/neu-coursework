import mysql.connector

CFG = {
    "host": "127.0.0.1",
    "port": 3306,
    "database": "sanjose",
    "user": "lab9user",
    "password": "Lab9Pass_123!",
}


def connect():
    return mysql.connector.connect(**CFG)


def exec_sql(conn, sql):
    cur = conn.cursor()
    cur.execute(sql)
    cur.close()


def fetch(conn, label, sql="SELECT * FROM ACCT ORDER BY ID"):
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    print(label)
    if rows:
        for row in rows:
            print("   ", row)
    else:
        print("    EMPTY RESULT")
    print()
    return rows


def reset_acct(rows):
    conn = connect()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS ACCT")
    cur.execute("CREATE TABLE ACCT (ID VARCHAR(10), BAL INT)")
    cur.executemany("INSERT INTO ACCT VALUES (%s, %s)", rows)
    conn.commit()
    cur.close()
    conn.close()


def a3_default_isolation():
    print("=" * 70)
    print("A3: Multiple Transactions with default isolation")
    print("=" * 70)

    # This is the expected state after A2 first run and second rollback.
    reset_acct([("A", 200), ("B", 900)])

    tx1 = connect()
    tx2 = connect()
    tx1.autocommit = False
    tx2.autocommit = False

    exec_sql(tx1, "UPDATE ACCT SET BAL = 100 WHERE ID = 'A'")

    fetch(tx2, "A3 Step 3 - Tx2 SELECT before Tx1 COMMIT:")

    tx1.commit()

    fetch(tx2, "A3 Step 5 - Tx2 SELECT after Tx1 COMMIT but before Tx2 COMMIT:")

    tx2.commit()

    fetch(tx2, "A3 Step 7 - Tx2 SELECT after Tx2 COMMIT:")

    tx1.close()
    tx2.close()


def b1_read_uncommitted():
    print("=" * 70)
    print("B1: READ UNCOMMITTED")
    print("=" * 70)

    reset_acct([("A", 100), ("B", 1000)])

    tx1 = connect()
    tx2 = connect()

    exec_sql(tx2, "SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")

    tx1.autocommit = False
    tx2.autocommit = False

    fetch(tx1, "B1 Step 3 - Tx1 initial SELECT:")

    exec_sql(tx1, "UPDATE ACCT SET BAL = 200 WHERE ID = 'A'")

    fetch(tx1, "B1 Step 5 - Tx1 SELECT after UPDATE, before ROLLBACK:")
    fetch(tx2, "B1 Step 6 - Tx2 SELECT under READ UNCOMMITTED:")

    tx1.rollback()

    fetch(tx1, "B1 Step 8 - Tx1 SELECT after ROLLBACK:")
    fetch(tx2, "B1 Step 9 - Tx2 SELECT after Tx1 ROLLBACK:")

    tx2.commit()

    tx1.close()
    tx2.close()


def b2_read_committed():
    print("=" * 70)
    print("B2: READ COMMITTED")
    print("=" * 70)

    reset_acct([("A", 100), ("B", 1000)])

    tx1 = connect()
    tx2 = connect()

    exec_sql(tx2, "SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")

    tx1.autocommit = False
    tx2.autocommit = False

    fetch(tx1, "B2 Step 3 - Tx1 initial SELECT:")

    exec_sql(tx1, "UPDATE ACCT SET BAL = 200 WHERE ID = 'A'")

    fetch(tx1, "B2 Step 5 - Tx1 SELECT after UPDATE, before COMMIT:")
    fetch(tx2, "B2 Step 6 - Tx2 SELECT under READ COMMITTED before Tx1 COMMIT:")

    tx1.commit()

    fetch(tx1, "B2 Step 8 - Tx1 SELECT after COMMIT:")
    fetch(tx2, "B2 Step 9 - Tx2 SELECT after Tx1 COMMIT:")

    tx2.commit()

    tx1.close()
    tx2.close()


def b3_repeatable_read():
    print("=" * 70)
    print("B3: REPEATABLE READ")
    print("=" * 70)

    reset_acct([("A", 100), ("B", 1000)])

    tx1 = connect()
    tx2 = connect()

    exec_sql(tx2, "SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ")

    tx1.autocommit = False
    tx2.autocommit = False

    fetch(tx2, "B3 Step 3 - Tx2 SELECT ID WHERE BAL = 200 before insert:",
          "SELECT ID FROM ACCT WHERE BAL = 200 ORDER BY ID")

    fetch(tx1, "B3 Step 4 - Tx1 initial SELECT:")

    exec_sql(tx1, "INSERT INTO ACCT VALUES ('C', 200)")

    fetch(tx1, "B3 Step 6 - Tx1 SELECT after INSERT, before COMMIT:")

    fetch(tx2, "B3 Step 7 - Tx2 SELECT before Tx1 COMMIT:",
          "SELECT ID FROM ACCT WHERE BAL = 200 ORDER BY ID")

    tx1.commit()

    fetch(tx1, "B3 Step 9 - Tx1 SELECT after COMMIT:")

    fetch(tx2, "B3 Step 10 - Tx2 SELECT after Tx1 COMMIT, same Tx2 transaction:",
          "SELECT ID FROM ACCT WHERE BAL = 200 ORDER BY ID")

    tx2.commit()

    tx1.close()
    tx2.close()


if __name__ == "__main__":
    a3_default_isolation()
    b1_read_uncommitted()
    b2_read_committed()
    b3_repeatable_read()
