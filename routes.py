import sqlite3
from app import app
from flask import render_template, request, redirect, url_for, session, g, flash
from werkzeug.security import check_password_hash
from models import cadastro_contador, cadastro_empresa, get_drive_service, pesquisa_pasta_drive_id_drive, pesquisa_pasta_drive_razao_social, vincular_contador_empresa, deletar_vinculo_empresa_contador
import os.path
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

#CONECTA AO DRIVE E PUXA OS ARQUIVOS
        #VARIAVEL COM OS ARQUIVOS
        FILE_LIST = None
        #PUXA ID DA EMPRESA DO FRONT
        ID_EMPRESA = request.args.get('empresa_id', type=int)
        if ID_EMPRESA:
            try:
                #BUSCA ID DO DRIVE
                ID_DRIVE = db.execute(
                    "SELECT g_drve_folder_id FROM empresa WHERE id = ?",
                    (ID_EMPRESA,)
                ).fetchone()
                sucesso, FILES = pesquisa_pasta_drive_id_drive(ID_DRIVE)

                if sucesso:
                    FILE_LIST = FILES
                else:
                    print(f"Erro ao buscar: {FILES}")
            except HttpError as e:
                return (False, "ERRO DE REQUISIÇÃO DRIVE")
#FIM - DRIVE

        username = session['user_name']
        is_admin = session.get('user_email') == admin_email
        
        return render_template(
            "dashboard.html", 
            username=username, 
            empresas=empresas,
            is_admin=is_admin,
            files=FILE_LIST
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
        form_type = request.form.get('form_type')
        NOME_DRIVE = request.form.get('nome_empresa_busca')
        if NOME_DRIVE:
            DRIVE_LIST = pesquisa_pasta_drive_razao_social(NOME_DRIVE)
            if not DRIVE_LIST:
                flash(f'Nenhuma pasta com o nome:{NOME_DRIVE}, foi encontrada no Google Drive', 'info')
        else:
            flash('Digite um nome para a busca.', 'warning')

    db = get_db()
    EMPRESAS = db.execute("SELECT id, razao_social FROM empresa ORDER BY razao_social").fetchall()

    return render_template(
        "admin_vincular_drive.html", 
        empresas=EMPRESAS,
        pastas = DRIVE_LIST
        )
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))