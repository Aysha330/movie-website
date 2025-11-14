import psycopg2

from psycopg2.extras import RealDictCursor

db = psycopg2.connect(
    "postgresql://ayisha:zz5ffyGUpRml2QhdMcAo2pQAGNlj8hxz@dpg-d4blgujipnbc73a65ug0-a.singapore-postgres.render.com/movienest_db"
)

cursor = db.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS watchlist (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    title VARCHAR(255),
    year VARCHAR(10),
    poster TEXT,
    overview TEXT
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS watched (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    title VARCHAR(255),
    year VARCHAR(10),
    poster TEXT,
    overview TEXT
);
""")

db.commit()
cursor.close()
db.close()

print("✅ Tables created successfully!")
