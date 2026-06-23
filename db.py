import mysql.connector

def get_db_connection():

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Anju@2005",
        database="freshsave"
    )

    return conn