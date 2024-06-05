from flask import Flask, redirect, url_for, session, render_template, request
from authlib.integrations.flask_client import OAuth
from googleAuth import init_app, login, logout, authorize
from create_db import get_database_connection

import pandas as pd
import random
import mysql.connector

app = Flask(__name__)

app.secret_key = 'seu_segredo'

init_app(app)

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
    conn = get_database_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTO_INCREMENT, email VARCHAR(255) UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_urls
                 (id INTEGER PRIMARY KEY AUTO_INCREMENT, user_id INTEGER,
                 url TEXT, rate INTEGER DEFAULT 0, FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

initialize_database()


def generate_news_urls(user_id):
    conn = get_database_connection()
    c = conn.cursor()
    c.execute('SELECT id, url, rate FROM user_urls WHERE user_id = %s', (user_id,))
    urls = c.fetchall()
    conn.close()
    if not urls:
        news_data = pd.read_csv('data/news.csv')
        selected_urls = random.sample(news_data['url'].tolist(), 5)
        conn = get_database_connection()
        c = conn.cursor()

        for url in selected_urls:
            c.execute('INSERT INTO user_urls (user_id, url, rate) VALUES (%s, %s, %s)', (user_id, url, 0))
        conn.commit()
        conn.close()
        return [(row[0], row[1], row[2]) for row in urls]
    else:
        return [(row[0], row[1], row[2]) for row in urls]

@app.route('/')
def index():
    email = session.get('email')
    if email:
        conn = get_database_connection()
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
        conn = get_database_connection()
        c = conn.cursor()
        c.execute('INSERT INTO users (email) VALUES (%s) ON DUPLICATE KEY UPDATE email=email', (email,))
        conn.commit()
        c.execute('SELECT id FROM users WHERE email = %s', (email,))
        user_id = c.fetchone()[0]
        session['user_id'] = user_id
        conn.close()
        print('Usuário autenticado com sucesso:', email)
        return redirect(url_for('dashboard'))
    except Exception as e:
        print('Erro durante a autorização:', e)
        return redirect('/')

@app.route('/dashboard')
def dashboard():
    email = session.get('email')
    if email:
        conn = get_database_connection()
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE email = %s', (email,))
        user_id = c.fetchone()[0]
        urls = generate_news_urls(user_id)
        conn.close()
        return render_template('dashboard.html', email=email, urls=urls)
    else:
        return redirect('/')

@app.route('/click')
def click():
    url_id = request.args.get('url_id')
    if url_id:
        conn = get_database_connection()
        c = conn.cursor()
        user_id = session.get('user_id')
        c.execute('UPDATE user_urls SET rate = rate + 1 WHERE user_id = %s AND id = %s', (user_id, url_id))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    else:
        return "Parâmetro 'url_id' ausente.", 400




if __name__ == '__main__':
    app.run(debug=True)

