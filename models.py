import sqlite3
import re
from email_validator import validate_email, EmailNotValidError
import json
import datetime
from werkzeug.security import generate_password_hash
import os
from dotenv import load_dotenv
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
load_dotenv()

DATABASE = "usuarios.db"

# COMEÇO -  FUNÇÕES AUXILIARES

#VALIDAÇÃO EMAIL
def valida_email(EMAIL):
    try:
       validate_email(EMAIL, check_deliverability=False)
       return True
    except EmailNotValidError as e:
       print(f"Log: {e}")
       return False

#VALIDAÇÃO CNPJ    
def valida_cnpj(CNPJ):
    CNPJ = re.sub(r'[^\d]', '', CNPJ)
    if len(CNPJ) == 14:
        return True
    else:
        return False
#FIM - FUNÇÕES AUXILIARES

#INICIO - FUNÇÕES SQL
    #INICIO - INSERTS 

        #INICIO- LOG
#INSERT PADRÃO DE LOG
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
        #FIM - LOG

        #INICIO - CADASTROS

#CADASTRO DE CONTADPR
def cadastro_contador(NOME, EMAIL, SENHA, EMPRESA=None):
    CONN = None
    try:
        CONN = sqlite3.connect(DATABASE)
        CONN.row_factory = sqlite3.Row
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
                #VERIFICAÇÃO DE VINCULAÇÃO A EMPRESA
                if EMPRESA:
                    #EXECUTA A FUNÇÃO SQL PARA BUSCAR A EMPRESA
                    SQL.execute("SELECT nome_fantasia FROM empresa WHERE id = ?", (EMPRESA,))
                    info_empresa = SQL.fetchone()
                    #ARMAZENA O RESULTADO E VERIFICA SE É A EMPRESA ADMINISTRADORA
                    if info_empresa and info_empresa['nome_fantasia'] == 'Admin':
                        #SE FOR, LIMPA O NOME ADMIN E CADASTRA O CONTADOR SEM VÍNCULO
                        EMPRESA = None
                        sucesso, mensagem = vincular_contador_empresa(SQL.lastrowid, EMPRESA)
                        return (True, f"Contador '{NOME}' cadastrado sem vinculo de empresa!")
                    else:
                        #SE NAO FOR, EXECUTA A VINCULAÇÃO E RETORNA O NOME DA EMPRESA VINCULADA
                        sucesso, mensagem = vincular_contador_empresa(SQL.lastrowid, EMPRESA)
                        nome_empresa = info_empresa['nome_fantasia']
                        #VERIFICA SE HOUVE SUCESSO NA VINCULAÇÃO
                        if sucesso:
                            return (True, f"Contador '{NOME}' cadastrado e vinculado na empresa {nome_empresa} com sucesso!")
                        else:
                            return (True, f"Contador '{NOME}' cadastrado com sucesso! Porém, falha ao vincular na empresa.")
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

#CADASTRO DE EMPRESA
def cadastro_empresa(RAZAO_SOCIAL, CNPJ, ID_DRIVE, FANTASIA, EMAIL, CONTATO, ID_CONTADOR=None):
    CONN = None
    try:
        CONN = sqlite3.connect(DATABASE)
        CONN.row_factory = sqlite3.Row
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
                #VERIFICAÇÃO SE TEM CONTADOR SELECIONADO
                if ID_CONTADOR:
                    #EXECUTA A FUNÇÃO SQL PARA BUSCAR O CONTADOR
                    SQL.execute("SELECT nome, email FROM contador WHERE id = ?", (ID_CONTADOR,))
                    resultado = SQL.fetchone()
                    #ARMAZENA O RESULTADO E VERIFICA SE É O CONTADOR ADMINISTRADOR
                    if resultado and resultado['email'] == 'adm@adm.com':
                        #SE FOR, LIMPA O NOME ADMIN E CADASTRA A EMPRESA SEM VÍNCULO
                        ID_CONTADOR = None 
                        sucesso, mensagem = vincular_contador_empresa(ID_CONTADOR, SQL.lastrowid)
                        return (True, f"Empresa '{FANTASIA or RAZAO_SOCIAL}' cadastrada com sucesso! Porém, sem vinculo de contador.")
                    else:
                        #SE NÃO FOR, RETORNA O NOME DO CONTADOR VINCULADO
                        nome_contador = resultado['nome']
                        sucesso, mensagem = vincular_contador_empresa(ID_CONTADOR, SQL.lastrowid)
                        return (True, f"Empresa '{FANTASIA or RAZAO_SOCIAL}' cadastrada e vinculada ao contador '{nome_contador}' com sucesso!")
                else:
                    #SE HOUVER FALHA NA VINCULAÇÃO, RETORNA A MENSAGEM DE ERRO
                    return (True, f"Empresa '{FANTASIA or RAZAO_SOCIAL}' cadastrada com sucesso! Porém, falha ao vincular ao contador: {mensagem}")
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

#VINCULAÇÃO DE EMPRESA A CONTADOR - INSERT NA TABELA CONTADOR_EMPRESA
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
        #FIM - CADASTROS

    #INICIO - UPDATES

#VINCULAR ID_DRIVE A EMPRESA QUE ESTAVA COM CAMPO NULL
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

    #INICIO - DELETES
        #DELETE DE CADASTROS

#EXCLUSÃO DE REGISTRO DE CONTADOR - NÃO RETIRE OS TIMEOUTS - PASSÍVEL DE BLOCK NO BD
def deletar_cadastro_contador(ID_CONTADOR,):
    CONN = None
    try:
        CONN = sqlite3.connect(DATABASE, timeout=10.0)
        SQL = CONN.cursor()
        SQL.execute("SELECT COUNT(*) FROM contador WHERE id = ?", (ID_CONTADOR,))
        if SQL.fetchone()[0] == 0:
            print(f"Contador não existe!")
            return (False, f"Contador não existe!")
        else:
            SQL.execute("SELECT * FROM contador WHERE id = ?", (ID_CONTADOR,))
            DATA = SQL.fetchall()
            SQL.execute("DELETE FROM contador_empresa WHERE id_contador = ?", (ID_CONTADOR,))
            SQL.execute("DELETE FROM contador WHERE id = ?", (ID_CONTADOR,))
            CONN.commit()
            DATA_LOG = {'DATA':DATA}
            insert_log(
                'DELETE',
                'SQL',
                'DELETE REGISTRO CONTADOR',
                ID_AUTOR=None,
                TIPO_ENTIDADE='CONTADOR',
                ID_ENTIDADE=ID_CONTADOR,
                DATA=DATA_LOG
            )
            print(f"Registro de contador apagado com sucesso.")
            return (True, f"Registro de contador apagado com sucesso")
    except sqlite3.Error as e:
        print(f"ERRO AO DELETAR REGISTRO DE CONTADOR - LOG:{e}")
        DATE_LOG = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with open(f"Log_DELETE_CONTADOR_{DATE_LOG}", "w") as txt_log:
            txt_log.write(f"ERRO_DELETE_EMPRESA_SQLog:{e}")
            return(False, f"ERRO AO DELETAR REGISTRO DE CONTADOR - LOG{e}")
    finally:
        if CONN:
            CONN.close()

#EXCLUSÃO DE REGISTRO DE EMPRESA - NÃO RETIRE OS TIMEOUTS - PASSÍVEL DE BLOCK NO BD
def deletar_cadastro_empresa(ID_EMPRESA,):
    CONN = None
    try:
        CONN = sqlite3.connect(DATABASE, timeout=10.0)
        SQL = CONN.cursor()
        SQL.execute("SELECT COUNT(*) FROM empresa WHERE id = ?", (ID_EMPRESA,))
        if SQL.fetchone()[0] == 0:
            print(f"Empresa não existe!")
            return (False, f"Empresa não existe!")
        else:
            SQL.execute("SELECT * FROM empresa WHERE id = ?", (ID_EMPRESA,))
            DATA = SQL.fetchall()
            SQL.execute("DELETE FROM contador_empresa WHERE id_empresa = ?", (ID_EMPRESA))
            SQL.execute("DELETE FROM empresa WHERE id = ?", (ID_EMPRESA,))
            CONN.commit()
            DATA_LOG = {'data':DATA}
            insert_log(
                'DELETE',
                'SQL',
                'DELETE REGISTRO EMPRESA',
                ID_AUTOR=None,
                TIPO_ENTIDADE='EMPRESA',
                ID_ENTIDADE=ID_EMPRESA,
                DATA=DATA_LOG
            )
            print(f"Regsitro de empresa apagado com sucesso!")
            return (True, f"Registro de empresa apagado com sucesso!")
    except sqlite3.Error as e:
        print(f"ERRO AO DELETER EMPRESA - LOG:{e}")
        DATE_LOG = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with open(f"ERROR_LOG_DELETE_EMPRESA_{DATE_LOG}", "w") as txt_log:
            txt_log.write(f"ERROR_DELETE_EMPRESA_LOG_{e}")
            return (False, f"ERRO AO DELETER EMPRESA - LOG:{e}")
    finally:
        if CONN:
            CONN.close()
#EXLCUSÃO DE REGISTRO DE VÍNCULO DE EMPRESA E CONTADOR - NÃO RETIRE OS TIMEOUTS - PASSÍVEL DE BLOCK NO BD
def deletar_vinculo_empresa_contador(ID_CONTADOR, ID_EMPRESA):
    CONN = None
    try:
        CONN = sqlite3.connect(DATABASE, timeout=10.0)
        SQL = CONN.cursor()
        SQL.execute("SELECT COUNT(*) FROM contador_empresa WHERE id_contador = ? AND id_empresa = ?", (ID_CONTADOR, ID_EMPRESA,))
        if SQL.fetchone()[0] == 0:
            print(f"NÃO EXISTE VÍNCULO ENTRE ESSA EMPRESA E CONTADOR")
            return (False, f"Não existe vínculo entre essa empresa e contador!")
        SQL.execute("SELECT COUNT(*) FROM contador WHERE id = ?", (ID_CONTADOR,))
        if SQL.fetchone()[0] == 0:
            print(f"CONTADOR NÃO EXISTE")
            return (False, f"Contador não existe!")
        SQL.execute("SELECT COUNT(*) FROM empresa WHERE id = ?", (ID_EMPRESA,))
        if SQL.fetchone()[0] == 0:
            print(f"EMPRESA NÃO EXISTE!")
            return (False, f"Empresa não existe!")
        SQL.execute("DELETE FROM contador_empresa WHERE id_contador = ? AND id_empresa = ?", (ID_CONTADOR, ID_EMPRESA,))
        CONN.commit()
        insert_log(
            'DELETE',
            'SQL',
            'DELETE_VINCULO_EMPRESA_CONTADOR',
            ID_AUTOR=None,
            TIPO_ENTIDADE="VINCULO_CONTADOR_EMPRESA",
            ID_ENTIDADE= ID_CONTADOR + ID_EMPRESA,
            DATA=None
        )
        print(f"VINCULO ENTRE EMPRESA E CONTADOR EXLCUÍDO COM SUCESSO!")
        return(True, f"Vínculo entre empresa e contadot excluído com sucesso!")
    except sqlite3.Error as e:
        print(f"ERRO AO EXCLUIR REGISTRO DE VINCULO EMPRE CONTADOR - LOG:{e}")
        DATE_LOG = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with open(f"ERROR_LOG_DELETE_VINCULO_EMPRESA_CONTADOR_{DATE_LOG}", "w") as txt_log:
            txt_log.write(f"ERROR_LOG_DELETE_VINCULO_EMPRESA_CONTADOR_{e}")
            return (False, f"ERRO AO EXCLUIR REGISTRO DE VINCULO EMPRE CONTADOR - LOG:{e}")
    finally:
        if CONN:
            CONN.close()

    #FIM - DELETE

#FIM - FUNÇÕES SQL


#INICIOS - FUNÇÕES GOOLGE DRIVE

#INICIA SERVIÇO DE CONEXÃO A GOOGLE DRIVE - NECESSÁRIO "credentials.json" NA ROOT, ARQUIVO DEVE ESTAR VALIDADO NA CONTA DO DRIVE PELO GOOGLE CLOUD, 
# CASO ESTEJA ELE JÁ VAI CRIAR NA ROOT O "token.json" QUE É A AUTH_KEY DO API E FUNCIONARÁ CORRETAMENTE
#!!!!!!!!!!!!!!!COLOCA ESSES 2 JSON NO GIT IGNORE POR FAVOR, SE NÃO F, LITERALMENTE F, SÉRIO!!!!!!!!!!!!!!
def get_drive_service():
    CREDENCIAIS = None
    if os.path.exists("token.json"):
        CREDENCIAIS = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not CREDENCIAIS or not CREDENCIAIS.valid:
        if CREDENCIAIS and CREDENCIAIS.expired and CREDENCIAIS.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            CREDENCIAIS = flow.run_local_server(port=0)
        
        with open("token.json", "w") as token:
            token.write(CREDENCIAIS.to_json())
    return build("drive", "v3",  credentials=CREDENCIAIS)

#PESQUISA PASTAS NO DRIVE PELA RAZÃO SOCIAL
def pesquisa_pasta_drive_razao_social(NOME_DRIVE):
    DRIVE_LIST = None
    try:
        SERVICE = get_drive_service()
        CONSULTA_DRIVE = f"mimeType='application/vnd.google-apps.folder' and name contains '{NOME_DRIVE}' and trashed = false"
        RESULT  = SERVICE.files().list(
            q=CONSULTA_DRIVE,
            pageSize=100,
            fields="files(id, name, webViewLink)"
        ).execute()
        DRIVE_LIST = RESULT.get('files', [])
        return (True, DRIVE_LIST)
    except HttpError as e:
        print(f"ERRO AO CONSULTAR DRIVE - LOG:{e}")
        DATE_LOG = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with open(f"ERROR_CONSULTA_DRIVE_{DATE_LOG}", "w") as txt_log:
            txt_log.write(f"ERROR_CONSULTA_DRIVE_LOG_{e}")
            return (False, f"ERROR_CONSULTA_DRIVE_LOG:{e}")
        
def pesquisa_pasta_drive_id_drive(ID_DRIVE):
    FILE_LIST = None
    try:
        if ID_DRIVE and ID_DRIVE['g_drve_folder_id']:
            ID_DRIVE = ID_DRIVE['g_drve_folder_id']
            SERVICE = get_drive_service()
            CONSULTA_DRIVE = f"'{ID_DRIVE}' in parents and trashed = false"
            RESULTS = SERVICE.files().list(
                q=CONSULTA_DRIVE,
                pageSize=100,
                fields="files(id, name, webViewLink)"
                ).execute()
        FILE_LIST = RESULTS.get("files", [])
        return(True, FILE_LIST)
    except HttpError as e:
            print(f"ERRO AO ACESSAR DRIVE - LOG{e}")
            DATE_LOG = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            with open(f"ERROR_CONSULTA_DRIVE_{DATE_LOG}", "w") as txt_log:
                txt_log.write(f"ERROR_CONSULTA_DRIVE_LOG_{e}")
                return (False, f"ERROR_CONSULTA_DRIVE_LOG:{e}")