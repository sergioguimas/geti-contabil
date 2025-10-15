import sqlite3
from werkzeug.security import generate_password_hash

print("--- Criador de Usuário Contador ---")


email = input("Digite o email do contador: ")
nome = input("Digite o nome do contador: ")
senha = input("Digite a senha do contador: ")


hash_senha = generate_password_hash(senha)

try:

    connection = sqlite3.connect('usuarios.db')
    cursor = connection.cursor()


    cursor.execute(
        "INSERT INTO contador (email, nome, senha_hash) VALUES (?, ?, ?)",
        (email, nome, hash_senha)
    )

    connection.commit()
    print(f"\nContador '{nome}' criado com sucesso!")

except sqlite3.IntegrityError:
    print(f"\nErro: O email '{email}' já existe no banco de dados.")
except Exception as e:
    print(f"\nOcorreu um erro: {e}")
finally:
    if connection:
        connection.close()