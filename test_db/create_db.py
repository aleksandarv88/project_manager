import psycopg2

def create_database():
    conn = psycopg2.connect(
        host = "localhost",
        dbname = "postgres",
        user = "postgres",
        password = "Ifmatoodlon@321"  # Replace with your actual password
    ) # entering the building
    conn.autocommit = True #explain this to me 
    cur = conn.cursor() # getting the clipboard
    cur.execute("CREATE DATABASE testdb;") # creating a new file using the clipboard
    cur.close() # returning the clipboard
    conn.close() # leaving the building

if __name__ == "__main__":
    create_database()