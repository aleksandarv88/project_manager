import psycopg2

conn = psycopg2.connect(
    host = 'localhost',
    database = 'postgres',
    user='postgres',
    password='Ifmatoodlon@321'  # replace with your actual password
)

cur = conn.cursor()
print("Database connection established.")

cur.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id SERIAL PRIMARY KEY,
        name TEXT,
        age INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("INSERT INTO projects (name, age) VALUES (%s, %s)", ("John Doe", 30))
cur.execute("INSERT INTO projects (name, age) VALUES (%s, %s)", ("Jane Smith", 25))
cur.execute("INSERT INTO projects (name, age) VALUES (%s, %s)", ("Alice Johnson", 28))

conn.commit()

cur.execute("SELECT * FROM projects;")
rows = cur.fetchall()
for row in rows:
    print(row)

cur.close()
conn.close()