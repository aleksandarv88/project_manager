import os
import psycopg2

def setup_users_table():
    conn = psycopg2.connect(
        host = "localhost",
        dbname = "testdb",
        user = "postgres",
        password = os.environ.get("PM_DB_PASSWORD", os.environ.get("PIPELINE_DB_PASSWORD", ""))
    )
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT,
            age INT
        )
    """)
    conn.commit()
    
    cur.execute("INSERT INTO users (name, age) VALUES (%s, %s);", ("Aleks", "30"))
    #cur.execute("DELETE FROM users WHERE name = %s;", ("Aleks",))
    conn.commit()

    cur.execute("SELECT * FROM users;")
    print(cur.fetchall())

    cur.close()
    conn.close()

if __name__ == "__main__":
    setup_users_table()
