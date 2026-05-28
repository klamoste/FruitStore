import sqlite3
conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
cur.execute('SELECT name, description FROM products_app_product LIMIT 20')
for row in cur.fetchall():
    print(f'{row[0]} - {row[1][:120].replace(chr(10), " ").replace(chr(13), " ")}')
conn.close()
