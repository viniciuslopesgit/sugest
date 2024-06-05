from flask import Flask, redirect, url_for, session, render_template, request
from authlib.integrations.flask_client import OAuth
from googleAuth import init_app, login, logout, authorize

import pandas as pd
import random

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

# Função para gerar URLs de notícias (substituindo a funcionalidade do MySQL)
def generate_news_urls(user_id):
    # Aqui você pode implementar a lógica para gerar URLs de notícias sem acessar o MySQL
    # Por exemplo, você pode ler de um arquivo CSV ou de uma API
    news_data = pd.read_csv('data/news.csv')
    selected_urls = random.sample(news_data['url'].tolist(), 5)
    return [(idx, url, 0) for idx, url in enumerate(selected_urls)]

# Rotas da sua aplicação
@app.route('/')
def index():
    email = session.get('email')
    if email:
        # Aqui você pode adicionar lógica para verificar se o usuário existe ou não
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
        # Aqui você pode adicionar lógica para autenticar o usuário sem usar o MySQL
        print('Usuário autenticado com sucesso:', email)
        return redirect(url_for('dashboard'))
    except Exception as e:
        print('Erro durante a autorização:', e)
        return redirect('/')

@app.route('/dashboard')
def dashboard():
    email = session.get('email')
    if email:
        # Aqui você pode adicionar lógica para recuperar URLs de notícias para o usuário sem usar o MySQL
        user_id = session.get('user_id')
        urls = generate_news_urls(user_id)
        return render_template('dashboard.html', email=email, urls=urls)
    else:
        return redirect('/')

@app.route('/click')
def click():
    print("CARREGOU")
    url_id = request.args.get('url_id')
    if url_id:
        # Aqui você pode adicionar lógica para registrar o clique do usuário sem usar o MySQL
        return redirect(url_for('dashboard'))
    else:
        return "Parâmetro 'url_id' ausente.", 400

if __name__ == '__main__':
    app.run(debug=True)
