from werkzeug.security import generate_password_hash
import mysql.connector

password = "admin123"  # change later
hashed_password = generate_password_hash(password)

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Pinchez@1",
    database="women_protection_platform"
)

cursor = conn.cursor()
cursor.execute(
    "INSERT INTO admins (username, password_hash) VALUES (%s, %s)",
    ("admin", hashed_password)
)

conn.commit()
cursor.close()
conn.close()

print("Admin created successfully.")
