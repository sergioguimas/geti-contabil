import sqlite3
import os
from dotenv import load_dotenv
load_dotenv()

connection = sqlite3.connect('usuarios.db')

with open('schema.sql') as f:
    connection.executescript(f.read())

connection.commit()
connection.close()

print("Banco de dados 'usuarios.db' inicializado com sucesso.")