import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

SUPERUSER = "postgres"
SUPERPASS = "Ifmatoodlon@321"
DB_NAME = "django_db"
DB_USER = "django_user"
DB_PASS = "Ifmatoodlon@321"

# connect as superuser
conn = psycopg2.connect(
    dbname="postgres",
    user=SUPERUSER,
    password=SUPERPASS,
    host="localhost"
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

# Create user if it doesn't exist
cur.execute(f"SELECT 1 FROM pg_roles WHERE rolname='{DB_USER}';")
if not cur.fetchone():
    cur.execute(f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASS}';")
    print(f"User {DB_USER} created")
else:
    print(f"User {DB_USER} already exists")

# Create database if it doesn't exist
cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}';")
if not cur.fetchone():
    cur.execute(f"CREATE DATABASE {DB_NAME} OWNER {DB_USER};")
    print(f"Database {DB_NAME} created")
else:
    print(f"Database {DB_NAME} already exists")

cur.close()
conn.close()
