import sqlite3
from app import app
from flask import render_template, request, redirect, url_for, session, g
from werkzeug.security import check_password_hash

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

        username = session['user_name']
        
        return render_template(
            "dashboard.html", 
            username=username, 
            empresas=empresas,
            files=None
        )

    return redirect(url_for('login'))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))