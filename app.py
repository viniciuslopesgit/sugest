from flask import Flask, redirect, url_for, session, render_template, request
from authlib.integrations.flask_client import OAuth
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import sqlite3
import numpy as np
import pandas as pd

# Carrega dados
news = pd.read_csv('data/news.csv', sep=',')
print(news.head())  # Exibe as primeiras linhas do DataFrame para verificação

# Selecionar colunas relevantes, incluindo a coluna 'url'
news_relevant = news[['url', 'name', 'language', 'bundle']]
print(news_relevant.head())  # Exibe as colunas selecionadas para verificação

# Preencher valores NaN com strings vazias
news_relevant = news_relevant.fillna('')

# Combina colunas relevantes em uma única string
news_relevant['content'] = news_relevant['name'] + ' ' + news_relevant['language'] + ' ' + news_relevant['bundle']

# Vetorização usando TF-IDF
tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(news_relevant['content'])

# Cálculo da similaridade utilizando kernel linear
cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

# Função para obter recomendações
def get_recommendations(url, cosine_sim=cosine_sim):
    # Verifica se a URL existe no DataFrame
    if url not in news_relevant['url'].values:
        raise ValueError(f"URL '{url}' não encontrada no dataset.")
    idx = news_relevant[news_relevant['url'] == url].index[0]
    # Calcula as similaridades e ordena
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_indices = [i[0] for i in sim_scores[1:11]]
    # Retorna as URLs recomendadas
    return news_relevant['url'].iloc[sim_indices]

# Exemplo de recomendação
try:
    print(get_recommendations('example_website_url'))
except ValueError as e:
    print(e)

app = Flask(__name__)

# Carregar o arquivo CSV NEWS
df_ratings = pd.read_csv('data/news.csv')

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

# Função para inicializar o banco de dados
def initialize_database():
    conn = sqlite3.connect('sites.db')
    c = conn.cursor()
    
    # Criar a tabela de usuários, se não existir
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE)''')
    
    # Criar a tabela de interações, se não existir
    c.execute('''CREATE TABLE IF NOT EXISTS interactions
                 (user_id INTEGER, site TEXT, rate INTEGER,
                 FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    # Verificar se a coluna 'rate' já existe
    c.execute("PRAGMA table_info(interactions)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'rate' not in columns:
        # Adicionar a coluna 'rate', se não existir
        c.execute('ALTER TABLE interactions ADD COLUMN rate INTEGER')

        # Criar a tabela de URLs, se não existir
    c.execute('''CREATE TABLE IF NOT EXISTS user_urls
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                 url TEXT, FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    initialize_database()
    email = session.get('email')
    if email:
        # Verifica se é a primeira sessão do usuário
        conn = sqlite3.connect('sites.db')
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        if not user:
            # É a primeira sessão do usuário, gera e salva os URLs
            user_id = c.execute('INSERT INTO users (email) VALUES (?)', (email,)).lastrowid
            news_urls = generate_news_urls()  # Função para gerar os URLs de notícias
            for url in news_urls:
                c.execute('INSERT INTO user_urls (user_id, url) VALUES (?, ?)', (user_id, url))
            conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))  # Se o usuário estiver autenticado, redirecionar para a dashboard
    else:
        return render_template('index.html')
    
def generate_news_urls():
    # Selecionar aleatoriamente 5 URLs do arquivo CSV
    selected_urls = news['url'].sample(n=5, replace=False).tolist()
    return selected_urls# Retorna 5 URLs aleatórias

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
        
        # Armazena o usuário no banco de dados
        conn = sqlite3.connect('sites.db')
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO users (email) VALUES (?)', (email,))
        conn.commit()
        
        # Recupera o ID do usuário e armazena na sessão
        c.execute('SELECT id FROM users WHERE email = ?', (email,))
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
        return render_template('dashboard.html', email=email)
    else:
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

# Sistema de recomendação

if __name__ == '__main__':
    app.run(debug=True)
