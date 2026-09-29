"""Create deterministic synthetic data; never overwrite an existing database."""
import sqlite3
from pathlib import Path


def seed(path='demo.db'):
    path = Path(path)
    if path.exists():
        raise FileExistsError('Refusing to overwrite an existing database')
    connection = sqlite3.connect(path)
    try:
        connection.executescript('''
        CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL);
        CREATE TABLE orders (id INTEGER PRIMARY KEY, product_id INTEGER REFERENCES products(id),
            region TEXT NOT NULL, quantity INTEGER NOT NULL, revenue_cents INTEGER NOT NULL);
        ''')
        connection.executemany('INSERT INTO products VALUES (?, ?, ?)', [(1, 'Notebook', 'Stationery'), (2, 'Desk lamp', 'Lighting'), (3, 'Mug', 'Kitchen')])
        connection.executemany('INSERT INTO orders VALUES (?, ?, ?, ?, ?)',
            [(i, 1+(i%3), ['North', 'South', 'West'][i%3], 1+(i%4), (1+(i%4))*[500, 2500, 1200][i%3]) for i in range(1, 121)])
        connection.commit()
    finally:
        connection.close()

if __name__ == '__main__':
    seed()
