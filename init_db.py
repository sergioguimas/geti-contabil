import sqlite3

connection = sqlite3.connect('usuarios.db')

with open('schema.sql') as f:
    connection.executescript(f.read())

connection.commit()
connection.close()

print("Banco de dados 'usuarios.db' inicializado com sucesso.")