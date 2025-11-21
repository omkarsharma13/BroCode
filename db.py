# db.py
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        dbname="mini_uber",
        user="postgres",
        password="omkar13",
        host="localhost",
        port="5432",
        cursor_factory=RealDictCursor
    )
