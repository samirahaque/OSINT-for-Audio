import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    """Create a database connection to a SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connected to {db_file}. SQLite version: {sqlite3.version}")
    except Error as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    """Create a table from the create_table_sql statement."""
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def insert_user(conn, user):
    """Insert a new user into the users table."""
    sql = ''' INSERT INTO users(username, password)
              VALUES(?,?) '''
    cur = conn.cursor()
    cur.execute(sql, user)
    conn.commit()
    return cur.lastrowid

def main():
    database = "users.db"

    sql_create_users_table = """ CREATE TABLE IF NOT EXISTS users (
                                        id integer PRIMARY KEY,
                                        username text NOT NULL,
                                        password text NOT NULL
                                    ); """

    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        # create users table
        create_table(conn, sql_create_users_table)
        # check if the users table is empty and insert default credentials
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()
        if len(users) == 0:
            # Inserting default credentials
            default_user = ('admin', 'admin') # This is an insecure example. Hash passwords in a real application.
            user_id = insert_user(conn, default_user)
            print(f"Default credentials added with user id: {user_id}")
        else:
            print("Database already contains users. No default credentials added.")
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    main()
