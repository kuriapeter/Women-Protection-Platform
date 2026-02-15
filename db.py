import mysql.connector

def get_db_connection():
    
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Pinchez@1",
        database="women_protection_platform"
    )
