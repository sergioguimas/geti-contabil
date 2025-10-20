#codigo teste para adicionar contadores no banco
#obsoleto
from models import cadastro_contador

print("--- Criador de Usuário Contador ---")

email = input("Digite o email do contador: ")
nome = input("Digite o nome do contador: ")
senha = input("Digite a senha do contador: ")

cadastro_contador(nome, email, senha)