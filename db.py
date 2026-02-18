import mysql.connector

def get_db_connection():
    
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Pinchez@1",
        database="women_protection_platform"
    )
def get_services():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM services")
    services = cursor.fetchall()
    cursor.close()
    conn.close()
    return services