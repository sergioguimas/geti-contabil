import sqlite3

# --- DADOS DE EXEMPLO ---
# Adicione aqui as empresas que você quer criar e associar
empresas_para_adicionar = [
    {
        "razao_social": "Padaria Pão Quente Ltda.",
        "cnpj": "11.222.333/0001-44",
        "nome_fantasia": "Padaria Sonho Doce",
        "email": "contato@sonhodoce.com",
        "contato": "(31) 99999-1111"
    },
    {
        "razao_social": "Tecnologia Rápida S.A.",
        "cnpj": "44.555.666/0001-77",
        "nome_fantasia": "TechFast",
        "email": "financeiro@techfast.com",
        "contato": "(11) 98888-2222"
    }
]
# ID do contador que será o "dono" dessas empresas (1 é o ID do adm@adm.com)
id_contador_admin = 1
# -------------------------

connection = sqlite3.connect('usuarios.db')
cursor = connection.cursor()

print("Inserindo e associando empresas...")

for empresa in empresas_para_adicionar:
    try:
        # Insere a empresa na tabela 'empresa'
        cursor.execute(
            """INSERT INTO empresa (razao_social, cnpj, nome_fantasia, email, contato)
               VALUES (?, ?, ?, ?, ?)""",
            (empresa["razao_social"], empresa["cnpj"], empresa["nome_fantasia"], empresa["email"], empresa["contato"])
        )
        # Pega o ID da empresa que acabamos de inserir
        id_nova_empresa = cursor.lastrowid
        
        # Cria a associação na tabela 'contador_empresa'
        cursor.execute(
            "INSERT INTO contador_empresa (id_contador, id_empresa) VALUES (?, ?)",
            (id_contador_admin, id_nova_empresa)
        )
        print(f"  - Empresa '{empresa['nome_fantasia']}' criada e associada com sucesso.")
        
    except sqlite3.IntegrityError:
        print(f"  - Aviso: A empresa com CNPJ '{empresa['cnpj']}' já existe no banco de dados.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

connection.commit()
connection.close()

print("\nProcesso finalizado!")