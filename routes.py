import sqlite3
import io
import os.path
import zipfile
from app import app
from flask import (
    render_template, request, redirect, url_for, session, g, flash, send_file, Response
)
from werkzeug.security import check_password_hash
from googleapiclient.http import MediaIoBaseDownload
from models import (
    cadastro_contador, cadastro_empresa, get_drive_service, 
    pesquisa_pasta_drive_id_drive, pesquisa_pasta_drive_razao_social, 
    vincular_contador_empresa, deletar_vinculo_empresa_contador,
    get_folder_details, vincular_empresa_drive, get_file_download_request_and_name
)
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

DATABASE = 'usuarios.db'
admin_email = os.getenv("ADMIN_EMAIL")

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/")
def home():
    if 'user_name' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'user_name' in session:
        return redirect(url_for('dashboard'))

    error = None
    if request.method == 'POST':
        email_form = request.form['email']
        password_form = request.form['password']
        
        db = get_db()
        user = db.execute(
            'SELECT * FROM contador WHERE email = ?', (email_form,)
        ).fetchone()

        if user is None:
            error = 'E-mail não encontrado. Tente novamente.'
        elif not check_password_hash(user['senha_hash'], password_form):
            error = 'Senha incorreta.'
        else:
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['nome']
            session['user_email'] = user['email']
            return redirect(url_for('dashboard'))

    return render_template("login.html", error=error)

@app.route("/dashboard")
def dashboard():
    if 'user_name' in session:
        # Bloco de busca de empresas
        if session.get('user_email') != admin_email:
            db = get_db()
            empresas = db.execute(
                """
                SELECT e.id, e.nome_fantasia, e.razao_social
                FROM empresa e
                JOIN contador_empresa ce ON e.id = ce.id_empresa
                WHERE ce.id_contador = ?
                ORDER BY e.nome_fantasia
                """,
                (session['user_id'],)
            ).fetchall()
        else:
            db = get_db()
            empresas = db.execute(
                """
                SELECT id, nome_fantasia, razao_social
                FROM empresa
                ORDER BY nome_fantasia
                """
            ).fetchall()
        
        # Lógica de integração com o Google Drive
        FILE_LIST = None
        CURRENT_FOLDER = None
        PARENT_FOLDER_ID = None
        EMPRESA_ROOT_ID = None

        ID_EMPRESA = request.args.get('empresa_id', type=int)
        ID_PASTA_CLICADA = request.args.get('folder_id', type=str)
        SORT_KEY = request.args.get('sort', 'name')
        ID_SELECT = None

        db = get_db()
        
        # Saber qual é a pasta raiz da empresa
        if ID_EMPRESA:
            empresa_drive_info = db.execute(
                "SELECT g_drve_folder_id FROM empresa WHERE id = ?",
                (ID_EMPRESA,)
            ).fetchone()
            if empresa_drive_info and empresa_drive_info['g_drve_folder_id']:
                EMPRESA_ROOT_ID = empresa_drive_info['g_drve_folder_id']

        # Determinar qual pasta vamos exibir (a clicada ou a raiz da empresa)
        if ID_PASTA_CLICADA:
            ID_SELECT = ID_PASTA_CLICADA
        elif EMPRESA_ROOT_ID:
            ID_SELECT = EMPRESA_ROOT_ID
        
        # Se temos uma pasta para exibir
        if ID_SELECT:
            try:
                if SORT_KEY == 'date':
                    order_string = 'folder, modifiedTime desc'
                else:
                    order_string = 'folder, name'

                # Passar o 'order_string'
                sucesso_lista, FILES = pesquisa_pasta_drive_id_drive(ID_SELECT, order_string)
                if sucesso_lista:
                    FILE_LIST = FILES
                else:
                    print(f"Erro ao buscar lista de arquivos: {FILES}")
                    flash(f"Erro ao buscar arquivos: {FILES}", "error")

                # Busca os DETALHES da pasta atual (nome, pai)
                sucesso_detalhes, FOLDER_DETAILS = get_folder_details(ID_SELECT)
                if sucesso_detalhes:
                    CURRENT_FOLDER = FOLDER_DETAILS
                    
                    # Determinar o ID da pasta "Pai" para o botão "Voltar"
                    if FOLDER_DETAILS.get('parents'):
                        parent_id_from_api = FOLDER_DETAILS['parents'][0]
                        
                        # Só mostramos o botão "Voltar" se a pasta atual
                        # NÃO for a pasta raiz da empresa.
                        if ID_SELECT != EMPRESA_ROOT_ID:
                            PARENT_FOLDER_ID = parent_id_from_api
                else:
                    print(f"Erro ao buscar detalhes da pasta: {FOLDER_DETAILS}")
                    flash(f"Erro ao buscar detalhes da pasta: {FOLDER_DETAILS}", "error")

            except HttpError as e:
                flash(f"Erro de requisição ao Google Drive: {e}", "error")

        # FIM - DRIVE

        username = session['user_name']
        is_admin = session.get('user_email') == admin_email
        
        return render_template(
            "dashboard.html", 
            username=username, 
            empresas=empresas,
            is_admin=is_admin,
            files=FILE_LIST,
            current_folder=CURRENT_FOLDER,         # Passa os detalhes da pasta atual
            parent_folder_id=PARENT_FOLDER_ID,     # Passa o ID do pai
            empresa_id=ID_EMPRESA,                 # Passa o ID da empresa (para os links)
            current_sort=SORT_KEY                  # Passa o tipo de ordenação atual
        )

    return redirect(url_for('login'))


@app.route("/admin", methods=['GET', 'POST'])
def admin_page():
    if session.get('user_email') != admin_email:
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        if form_type == 'contador':
            nome = request.form.get('nome')
            email = request.form.get('email')
            senha = request.form.get('senha')
            empresa_id = request.form.get('empresa_id')
            sucesso, mensagem = cadastro_contador(nome, email, senha, empresa_id)
            if sucesso:
                flash(mensagem, 'success')
            else:
                flash(mensagem, 'error')
            

        elif form_type == 'empresa':
            razao_social = request.form.get('razao_social')
            nome_fantasia = request.form.get('nome_fantasia')
            cnpj = request.form.get('cnpj')
            empresa_email = request.form.get('empresa_email')
            contato = request.form.get('contato')
            drive_id = request.form.get('drive_id')
            contador_id = request.form.get('contador_id')
            sucesso, mensagem = cadastro_empresa(razao_social, cnpj, drive_id, nome_fantasia, empresa_email, contato, contador_id)
            if sucesso:
                flash(mensagem, 'success')
            else:
                flash(mensagem, 'error')
        return redirect(url_for('admin_page'))                
    db = get_db()
    contadores = db.execute("SELECT id, nome, email FROM contador ORDER BY nome").fetchall()
    empresas = db.execute("SELECT id, nome_fantasia, razao_social FROM empresa ORDER BY nome_fantasia").fetchall()                
    return render_template("admin_cadastros.html", contadores=contadores, empresas=empresas)

@app.route("/admin/vinculos", methods=['GET', 'POST'])
def admin_vinculos():
    if session.get('user_email') != admin_email:
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('dashboard'))
    
    db = get_db()

    if request.method == 'POST':
        contador_id = request.form.get('contador_id')
        empresa_id = request.form.get('empresa_id')
        action = request.form.get('action')

        if not contador_id or not empresa_id:
            flash('Por favor, selecione um contador e uma empresa.', 'error')
        else:
            if action == 'vincular':
                sucesso, mensagem = vincular_contador_empresa(contador_id, empresa_id)
                flash(mensagem, 'success' if sucesso else 'error')
            elif action == 'desvincular':
                sucesso, mensagem = deletar_vinculo_empresa_contador(contador_id, empresa_id)
                flash(mensagem, 'success' if sucesso else 'error')
        
        return redirect(url_for('admin_vinculos'))

    contadores = db.execute("SELECT id, nome, email FROM contador ORDER BY nome").fetchall()
    empresas = db.execute("SELECT id, nome_fantasia, razao_social FROM empresa ORDER BY nome_fantasia").fetchall()

    empresas_com_vinculos = db.execute("""
        SELECT 
            e.id, 
            e.nome_fantasia, 
            e.razao_social,
            c.nome AS contador_nome,
            c.email AS contador_email
        FROM empresa e
        LEFT JOIN contador_empresa ce ON e.id = ce.id_empresa
        LEFT JOIN contador c ON ce.id_contador = c.id
        ORDER BY e.nome_fantasia
    """).fetchall()
    
    return render_template("admin_vinculo.html", contadores=contadores, empresas=empresas, empresas_vinculadas=empresas_com_vinculos)

@app.route("/drive", methods=['GET', 'POST'])
def vincular_drive_page():
    if session.get('user_email') != admin_email:
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('dashboard'))
    
    DRIVE_LIST = []

    if request.method == 'POST':
        NOME_DRIVE = request.form.get('nome_empresa_busca')
        if NOME_DRIVE:
            DRIVE_LIST = pesquisa_pasta_drive_razao_social(NOME_DRIVE)
        else:
            flash('Digite um nome para a busca.', 'warning')
    db = get_db()
    EMPRESAS = db.execute("SELECT id, razao_social, nome_fantasia FROM empresa ORDER BY razao_social").fetchall()

    return render_template(
        "admin_vincular_drive.html", 
        empresas=EMPRESAS,
        files = DRIVE_LIST
        )

@app.route("/download/<string:file_id>")
def download_file(file_id):
    if 'user_name' not in session:
        return redirect(url_for('login'))
    
    try:
        # 1. Chamar a nova função "inteligente"
        sucesso, request_obj, download_name, mime_type = get_file_download_request_and_name(file_id)
        
        if not sucesso:
            flash(f"Não foi possível preparar o arquivo para download: {request_obj}", "error")
            return redirect(request.referrer or url_for('dashboard'))

        # 2. Baixar o arquivo para um buffer
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request_obj)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        fh.seek(0) # Retorna ao início do buffer

        # 3. Enviar o arquivo para o usuário com o nome e tipo corretos
        return send_file(
            fh,
            mimetype=mime_type,
            download_name=download_name,
            as_attachment=True
        )

    except HttpError as e:
        flash(f"Erro no Google Drive ao tentar baixar o arquivo: {e}", "error")
        return redirect(request.referrer or url_for('dashboard'))

@app.route("/download/batch", methods=["POST"])
def download_batch():
    if 'user_name' not in session:
        return redirect(url_for('login'))

    file_ids = request.form.getlist("file_ids")
    download_token = request.form.get("download_token")

    if not file_ids:
        flash("Nenhum arquivo foi selecionado para download.", "error")
        return redirect(request.referrer or url_for('dashboard'))

    zip_buffer = io.BytesIO()

    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            
            for file_id in file_ids:
                
                # 1. Chamar a nova função "inteligente" para cada arquivo
                sucesso, request_obj, download_name, mime_type = get_file_download_request_and_name(file_id)

                if not sucesso:
                    print(f"Erro ao preparar {file_id} para o zip: {request_obj}")
                    continue # Pula este arquivo

                # 2. Baixa o arquivo para um buffer temporário
                file_buffer = io.BytesIO()
                downloader = MediaIoBaseDownload(file_buffer, request_obj)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                
                file_buffer.seek(0)

                # 3. Escreve o conteúdo no Zip COM o nome correto (ex: "planilha.xlsx")
                zipf.writestr(download_name, file_buffer.read())
                
                file_buffer.close()

        # Prepara o buffer do Zip para ser enviado
        zip_buffer.seek(0)
        
        response = send_file(
            zip_buffer,
            mimetype='application/zip',
            download_name='arquivos_selecionados.zip',
            as_attachment=True
        )

        if download_token:
            response.set_cookie(f"download_token_{download_token}", "true", max_age=30) 
        
        return response

    except HttpError as e:
        flash(f"Erro no Google Drive ao tentar baixar os arquivos: {e}", "error")
        return redirect(request.referrer or url_for('dashboard'))
    except Exception as e:
        flash(f"Um erro inesperado ocorreu ao criar o arquivo zip: {e}", "error")
        return redirect(request.referrer or url_for('dashboard'))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/salvar_vinculo", methods=['POST'])
def salvar_vinculo():
    if session.get('user_email') != admin_email:
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('dashboard'))
    
    ID_EMPRESA = request.form.get('empresa_id')
    DRIVE_FOLDER_ID = request.form.get('folder_id')

    if ID_EMPRESA and DRIVE_FOLDER_ID:
        try:
            sucesso, mensagem = vincular_empresa_drive(ID_EMPRESA, DRIVE_FOLDER_ID)
            if sucesso:
                flash(mensagem, 'success')
                return redirect(url_for('vincular_drive_page'))
            else:
                flash(mensagem, 'error')
                return redirect(url_for('vincular_drive_page'))
        except Exception as e:
            flash(f"Erro ao vincular empresa ao Drive: {e}", 'error')
            return redirect(url_for('vincular_drive_page'))