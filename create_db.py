# create_db.py

import mysql.connector

def get_database_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='mabsam',
        database='db_sugest'
    )
    return conn
