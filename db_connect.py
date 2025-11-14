import mysql.connector

# Connect to MySQL
mydb = mysql.connector.connect(
    host="localhost",
    user="root",           # your MySQL username
    password="ainu@3386",   # your MySQL password
    database="movienest_db"
)

# Create a cursor to execute SQL commands
mycursor = mydb.cursor()

print("✅ Connected to MySQL database successfully!")
