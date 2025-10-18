import sqlite3
from app import app
from flask import render_template, request, redirect, url_for, session, g, flash
from werkzeug.security import check_password_hash
from models import cadastro_contador, cadastro_empresa

DATABASE = 'usuarios.db'

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

        FILE_LIST = None
        ID_EMPRESA = request.args.get('empresa_id', type=int)
        if ID_EMPRESA:
            try:
                EMPRESA_INFO = db.execute(
                    "SELECT f_drve_folder_id FROM empresa WHERE id = ?",
                    (ID_EMPRESA,)
                ).fetchone()
                if EMPRESA_INFO and EMPRESA_INFO['gdrve_folder_id']:
                    ID_FOLDER = EMPRESA_INFO['g_rdve_folder_id']
                    SERVICE = get_drive_service()
                    DRIVER_QUERY = f"{ID_FOLDER} in parents and trashed = false"
                    RESULTS = SERVICE.files().list(
                        Q=DRIVER_QUERY,
                        pageSize=100,
                        fields="files(id, name, webViewLink)"
                    ).execute()
                    FILE_LIST = RESULTS.get("files", [])
            except HttpError as e:
                flash(f"ERRO AO ACESSAR DRIVE - LOG{e}")
        username = session['user_name']

        is_admin = session.get('user_email') == 'adm@adm.com'
        
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
    if session.get('user_email') != 'adm@adm.com':
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

@app.route("/vinculos", methods=['GET', 'POST'])
def vinculos():
    if session.get('user_email') != 'adm@adm.com':
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('dashboard'))
        
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

        username = session['user_name']

        is_admin = session.get('user_email') == ''

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))