import sqlite3
import re
from email_validator import validate_email, EmailNotValidError
import json
import datetime
from werkzeug.security import generate_password_hash
import os
from dotenv import load_dotenv
load_dotenv()

DATABASE = "usuarios.db"

def valida_email(EMAIL):
    try:
       validate_email(EMAIL, check_deliverability=False)
       return True
    except EmailNotValidError as e:
       print(f"Log: {e}")
       return False
    
def valida_cnpj(CNPJ):
    CNPJ = re.sub(r'[^\d]', '', CNPJ)
    if len(CNPJ) == 14:
        return True
    else:
        return False

    
def insert_log(OPERACAO, NATUREZA, ACAO, ID_AUTOR=None, TIPO_ENTIDADE=None, ID_ENTIDADE=None, DATA=None):
    CONN = None
    try:
        CONN = sqlite3.connect(DATABASE)
        SQL = CONN.cursor()

        DATA_JSON = json.dumps(DATA) if DATA is not None else None
        SQL_INSERT = """ INSERT INTO log (operacao, natureza, acao, id_autor, tipo_entidade, id_entidade, descricao) VALUES(?, ?, ?, ?, ?, ?, ?)"""
        VALUES = (OPERACAO, NATUREZA, ACAO, ID_AUTOR, TIPO_ENTIDADE, ID_ENTIDADE, DATA_JSON)
        SQL.execute(SQL_INSERT, VALUES)
        CONN.commit()
    except sqlite3.Error as e:
        print(f"ERRO DE LOG: Falha ao registrar log no banco: {e}")
        DATE_LOG = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with open(f"Log_INSERT_LOG_{DATE_LOG}", "w") as txt_log:
            txt_log.write(f"ERRO_DE_REGISTRO-LOG-Falha ao efeturar registro-SQLog:{e}")
    finally:
        if CONN:
            CONN.close()




def cadastro_contador(NOME, EMAIL, SENHA):
    CONN = None
    try:
        CONN = sqlite3.connect(DATABASE)
        SQL = CONN.cursor()
        SQL.execute("SELECT COUNT(*) FROM contador WHERE email = ?", (EMAIL,))
        if SQL.fetchone()[0] > 0:
            return (False, f"O email '{EMAIL}' já está cadastrado no sistema.")
        else:
            if valida_email(EMAIL) == True:
                SENHA = generate_password_hash(SENHA)
                SQL_INSERT = "INSERT INTO contador (nome, email, senha_hash) VALUES(?, ?, ?);"
                VALUES = (NOME, EMAIL, SENHA)
                SQL.execute(SQL_INSERT, VALUES)
                CONN.commit()
                DATA_LOG = {'nome':NOME, 'email':EMAIL}
                insert_log(
                    'INSERT',
                    'SQL',
                    'REGISTRO DE CONTADOR',
                    ID_AUTOR=None,
                    TIPO_ENTIDADE='Contador',
                    ID_ENTIDADE=SQL.lastrowid,
                    DATA = DATA_LOG
                )
                return (True, f"Contador '{NOME}' cadastrado com sucesso!")
            else:
                return (False, f"O email '{EMAIL}' é inválido.")
    except sqlite3.Error as e:
        print(f"ERRO DE REGISTRO: Falha ao efetuar registro: {e}")
        DATE_LOG = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with open(f"Log_INSERT_CONTADOR_{DATE_LOG}", "w") as txt_log:
            txt_log.write(f"ERRO_DE_REGISTRO-CONTADOR-Falha ao efeturar registro-SQLog:{e}")
        return (False, "Ocorreu um erro no servidor ao tentar cadastrar o contador.")
    finally:
        if CONN:
            CONN.close()

def cadastro_empresa(RAZAO_SOCIAL, CNPJ, ID_DRIVE, FANTASIA, EMAIL, CONTATO):
    CONN = None
    try:
        CONN = sqlite3.connect(DATABASE)
        SQL = CONN.cursor()
        CNPJ = re.sub(r'[^\d]', '', CNPJ)
        SQL.execute("SELECT COUNT(*) FROM empresa WHERE cnpj = ?", (CNPJ,))
        if SQL.fetchone()[0] > 0:
            return (False, f"O CNPJ '{CNPJ}' já está cadastrado no sistema.")            
        else:
            SQL.execute("SELECT COUNT(*) FROM empresa WHERE g_drve_folder_id = ?", (ID_DRIVE,))
            if SQL.fetchone()[0] > 0:
                return (False, "Este ID do Google Drive já está associado a outra empresa.")
            elif valida_cnpj(CNPJ) == True:
                CNPJ = re.sub(r'[^\d]', '', CNPJ)
                SQL_INSERT = "INSERT INTO empresa (razao_social, cnpj, g_drve_folder_id, nome_fantasia, email, contato) VALUES (?, ?, ?, ?, ?, ?);"
                VALUES = (RAZAO_SOCIAL, CNPJ, ID_DRIVE, FANTASIA, EMAIL, CONTATO)
                SQL.execute(SQL_INSERT, VALUES)
                CONN.commit()
                DATA_LOG = {'razao_social':RAZAO_SOCIAL, 'cnpj':CNPJ, 'id_drive':ID_DRIVE, 'email':EMAIL, 'contato':CONTATO}
                insert_log(
                    'INSERT',
                    'SQL',
                    'REGISTRO EMPRESA',
                    ID_AUTOR = None,
                    TIPO_ENTIDADE='Empresa',
                    ID_ENTIDADE=SQL.lastrowid,
                    DATA=DATA_LOG
                )
            else:
                return (False, f"CNPJ: {CNPJ} é inválido!")
    except sqlite3.Error as e:
        print(f"ERRO DE REGISTRO: Falha ao efetuar registro: {e}")
        DATE_LOG = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with open(f"Log_INSERT_EMPRESA_{DATE_LOG}", "w") as txt_log:
            txt_log.write(f"ERRO_DE_REGISTRO-EMPRESA-Falha ao efeturar registro-SQLog:{e}")
        return (False, "Ocorreu um erro no servidor ao tentar cadastrar a empresa.")
    finally:
        if CONN:
            CONN.close()

def vincular_contador_empresa(ID_CONTADOR, ID_EMPRESA):
    CONN = None
    try:
        CONN = sqlite3.connect(DATABASE)
        SQL = CONN.cursor()
        SQL.execute("SELECT COUNT(*) FROM contador_empresa WHERE id_contador = ? AND id_empresa = ?", (ID_CONTADOR, ID_EMPRESA,))
        if SQL.fetchone()[0] > 0:
            print("Empresa já associada a contador!")
            return (False, "Esta empresa já está associada a este contador.")
        SQL.execute("SELECT COUNT(*) FROM contador WHERE id = ?", (ID_CONTADOR,))
        if SQL.fetchone()[0] == 0:
            print("Contador não existe!")
            return (False, "Contador não existe!")
        SQL.execute("SELECT COUNT(*) FROM empresa WHERE id = ?", (ID_EMPRESA,))
        if SQL.fetchone()[0] == 0:
            print("Empresa não existe!")
            return (False, "Empresa não existe!")
        SQL_INSERT = "INSERT INTO contador_empresa (id_contador, id_empresa) VALUES (?, ?)"
        VALUES = (ID_CONTADOR, ID_EMPRESA)
        SQL.execute(SQL_INSERT, VALUES)
        CONN.commit()
        DATA_LOG = {'id_contador':ID_CONTADOR, 'id_empresa':ID_EMPRESA}
        insert_log(
            'INSERT',
            'SQL',
            'REGISTRO VINCULACAO CONTADOR_EMPRESA',
            ID_AUTOR=None,
            TIPO_ENTIDADE='Conexao_Empresa_Contador',
            ID_ENTIDADE=SQL.lastrowid,
            DATA=DATA_LOG
        )
        return (True, "Vinculação efetuada com sucesso!")
    except sqlite3.Error as e:
        print(f"ERRO DE REGISTRO: Falha ao efetuar o registro - {e}")
        DATE_LOG = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with open(f"Log_INSERT_CONT_EMPR_{DATE_LOG}", "w") as txt_log:
            txt_log.write(f"ERRO_DE_REGISTRO-CONTADOR_EMPRESA-Falha ao efeturar registro - SQLog:{e}")
        return (False, f"Erro ao efetuar a vinculação: {e}")
    finally:
        if CONN:
            CONN.close()

def vincular_empresa_drive(ID_EMPRESA, ID_DRIVE):
    CONN = None
    try:
        CONN = sqlite3.connect(DATABASE)
        SQL = CONN.cursor()
        SQL.execute("SELECT COUNT(*) FROM empresa WHERE id = ?", (ID_EMPRESA,))
        if SQL.fetchone()[0] == 0:
            return (False, "Empresa não existe!")
        else:
            SQL_UPDATE ="UPDATE empresa SET g_drve_folder_id = ? WHERE id = ?"
            VALUES = (ID_DRIVE, ID_EMPRESA)
            SQL.execute(SQL_UPDATE, VALUES)
            CONN.commit()
            DATA_LOG = {'id_empresa':ID_EMPRESA, 'id_drive': ID_DRIVE}
            insert_log(
                'UPDATE',
                'SQL',
                'VINCULAÇÃO EMPRESA A DRIVE',
                ID_AUTOR=None,
                TIPO_ENTIDADE='Empresa',
                ID_ENTIDADE=ID_EMPRESA,
                DATA=DATA_LOG
            )
            return (True, "Vinculação efetuada com sucesso!")
    except sqlite3.Error as e:
        print(f"ERRO DE ALTERAÇÃO: Falha ao alterar o registro - {e}")
        DATE_LOG = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with open(f"Log_UPDATE_EMPRESA_{DATE_LOG}", "w") as txt_log:
            txt_log.write(f"ERRO_DE_UPDATE-EMPRESA-Falha ao alterar registro - SQLog:{e}")
        return (False, f"Erro ao efetuar a vinculação: {e}")
    finally:
        if CONN:
            CONN.close()
