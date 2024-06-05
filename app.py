from flask import Flask, redirect, url_for, session, render_template, request
from authlib.integrations.flask_client import OAuth
from create_db import get_database_connection
import mysql.connector
import pandas as pd
import random

app = Flask(__name__)

app.secret_key = 'seu_segredo'
app.config['GOOGLE_CLIENT_ID'] = '213167038682-1ch7jaaqftacmkoc6c127qim1te6kjoh.apps.googleusercontent.com'
app.config['GOOGLE_CLIENT_SECRET'] = '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'

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid profile email'},
)

def initialize_database():
    conn = get_database_connection()  # Usa a função para obter a conexão
    c = conn.cursor()
    
    

    # Criar a tabela de usuários, se não existir
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTO_INCREMENT, email VARCHAR(255) UNIQUE)''')
    
    # Criar a tabela de URLs, se não existir
    c.execute('''CREATE TABLE IF NOT EXISTS user_urls
                 (id INTEGER PRIMARY KEY AUTO_INCREMENT, user_id INTEGER,
                 url TEXT, rate INTEGER DEFAULT 0, FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

# Inicializar o banco de dados quando o programa for iniciado
initialize_database()

def generate_news_urls(user_id):
    conn = get_database_connection()  # Usa a função para obter a conexão
    c = conn.cursor()
    
    c.execute('SELECT * FROM user_urls WHERE user_id = %s', (user_id,))
    urls = c.fetchall()
    conn.close()
    
    if not urls:  # Se não houver URLs associadas ao usuário
        # Carregar o arquivo CSV
        news_data = pd.read_csv('data/news.csv')
        
        # Selecionar aleatoriamente 5 URLs
        selected_urls = random.sample(news_data['url'].tolist(), 5)
        
        # Inserir os URLs gerados no banco de dados com a avaliação inicial
        conn = get_database_connection()  # Usa a função para obter a conexão
        c = conn.cursor()

        for url in selected_urls:
            c.execute('INSERT INTO user_urls (user_id, url, rate) VALUES (%s, %s, %s)', (user_id, url, 0))
        conn.commit()
        conn.close()
        
        return selected_urls
    else:
        return [url[2] for url in urls]  # Retorna as URLs já salvas no banco de dados

@app.route('/')
def index():
    email = session.get('email')
    if email:
        conn = get_database_connection()  # Usa a função para obter a conexão
        c = conn.cursor()

        c.execute('SELECT id FROM users WHERE email = %s', (email,))
        user = c.fetchone()
        if not user:
            c.execute('INSERT INTO users (email) VALUES (%s)', (email,))
            conn.commit()
            user_id = c.lastrowid
            news_urls = generate_news_urls(user_id)
        conn.close()
        return redirect(url_for('dashboard'))
    else:
        return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    email = session.get('email')
    if email:
        conn = get_database_connection()  # Usa a função para obter a conexão
        c = conn.cursor()

        c.execute('SELECT id FROM users WHERE email = %s', (email,))
        user_id = c.fetchone()[0]
        urls = generate_news_urls(user_id)
        conn.close()
        return render_template('dashboard.html', email=email, urls=urls)
    else:
        return redirect('/')

@app.route('/visit/<int:url_id>')
def visit_url(url_id):
    email = session.get('email')
    if email:
        conn = get_database_connection()  # Usa a função para obter a conexão
        c = conn.cursor()

        c.execute('UPDATE user_urls SET rate = rate + 1 WHERE id = %s', (url_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    else:
        return redirect('/')








# Restante do código permanece igual...



@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect('/')

@app.route('/auth')
def authorize():
    try:
        token = google.authorize_access_token()
        user_info_resp = google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
        user_info = user_info_resp.json()
        email = user_info.get('email')
        session['email'] = email
        
        conn = sqlite3.connect('sites.db')
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO users (email) VALUES (?)', (email,))
        conn.commit()
        
        c.execute('SELECT id FROM users WHERE email = ?', (email,))
        user_id = c.fetchone()[0]
        session['user_id'] = user_id
        
        conn.close()
        
        print('Usuário autenticado com sucesso:', email)
        return redirect(url_for('dashboard'))
    except Exception as e:
        print('Erro durante a autorização:', e)
        return redirect('/')

@app.route('/interact', methods=['POST'])
def interact():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    site = request.form.get('site')
    rate = request.form.get('rate')  # Captura o valor da avaliação
    
    conn = sqlite3.connect('sites.db')
    c = conn.cursor()
    c.execute('INSERT INTO interactions (user_id, site, rate) VALUES (?, ?, ?)', (user_id, site, rate))
    conn.commit()
    conn.close()
    
    return redirect('/dashboard')




if __name__ == '__main__':
    app.run(debug=True)
