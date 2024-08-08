from flask import Flask, redirect, url_for, session, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from datetime import datetime
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text, func
import pandas as pd
import random
import psycopg2
import requests
import os

load_dotenv()
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('POSTGRES_LOGIN')
db = SQLAlchemy(app)

app.secret_key = 'seu_segredo'
app.config['GOOGLE_CLIENT_ID'] =  os.getenv('GOOGLE_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id = os.getenv('GOOGLE_ID'),
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url = 'https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs = {'scope': 'openid profile email'},
)


# -------------------------------- FUNÇÕES --------------------------------------

# Isere dados da conta gmail do usuário no banco de dados
class tbl_user(db.Model):
    __tablename__ = 'tbl_user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

    def __init__(self, email, name, password=None):
        self.email = email
        self.name = name
        if password:
            self.password = generate_password_hash(password)

class tbl_user_fav(db.Model):
    __tablename__ = 'tbl_user_fav'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    site_id = db.Column(db.Integer)
    rate = db.Column(db.Integer)

    def __init__(self, user_id, site_id, rate):
        self.user_id = user_id
        self.site_id = site_id
        self.rate = rate

    def update_rate(self):
        self.rate += 1

class tbl_sites(db.Model):
    __tablename__ = 'tbl_sites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String())
    name = db.Column(db.String(100))

    def __init__(self, user_id=user_id, url=url, description=description, name=name):
        self.user_id = user_id
        self.url = url
        self.description = description
        self.name = name


def insert_initial_user_favs(user_id):
    # Verifica se já existem favoritos para este usuário
    existing_count = tbl_user_fav.query.filter_by(user_id=user_id).count()
    if existing_count > 0:
        return
    
    # Seleciona aleatoriamente 5 URLs da tabela tbl_sites
    try:
        engine = create_engine(os.getenv('POSTGRES_LOGIN'))
        query = "SELECT id FROM tbl_sites ORDER BY random() LIMIT 5"
        tbl_sites = pd.read_sql(query, con=engine)
    except Exception as e:
        print("Erro ao conectar ao banco de dados:", e)
        return
    
    for _, row in tbl_sites.iterrows():
        #tbl_user_fav:
        #user_id, site_id, rate
        site_id = int(row['id'])
        rate = 1
        new_fav = tbl_user_fav(user_id=user_id, site_id=site_id, rate=rate)
        db.session.add(new_fav)
    
    db.session.commit()


def jaccard_similarity(set1, set2):
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union

def recommend_sites_for_user():
    user_id = session.get('user_id')

    if not user_id:
        print("Usuário não está logado.")
        return "Usuário não está logado."
    
    # Recolher IDs dos sites com rate igual a 1
    rated_urls = tbl_user_fav.query.filter_by(user_id=user_id, rate=1).all()
    rated_ids = [url.id for url in rated_urls]

    if not rated_ids:
        print("Nenhum site está favoritado")
        return "Nenhum site está favoritado"
    
    engine = create_engine(os.getenv('POSTGRES_LOGIN'))
    query = "SELECT id, name, url, description FROM url_data"
    url_data = pd.read_sql(query, con=engine)

    rated_sites_data = url_data[url_data['id'].isin(rated_ids)]


    if rated_sites_data.empty:
        print("Nenhum dado correspondente encontrado no arquivo")
        return "Nenhum dado correspondente encontrado no arquivo"
    
    rated_keywords = set()
    for description in rated_sites_data['description']:
        if isinstance(description, str):
            rated_keywords.update(description.split(','))

    recommendations = []
    site_info = {}
    for index, row in url_data.iterrows():
        site_info[row['id']] = {'name': row['name'], 'url': row['url']}
        if row['id'] not in rated_ids:
            if isinstance(row['description'], str):
                site_keywords = set(row['description'].split(','))
                similarity = jaccard_similarity(rated_keywords, site_keywords)
                recommendations.append((row['id'], similarity))

    # Ordenar as recomendações pela maior similaridade
    recommendations.sort(key=lambda x: x[1], reverse=True)

    top_recommendations = recommendations[:50]

    # Adicionar informações de nome e URL aos resultados
    result = []
    for rec in top_recommendations:
        site_id = rec[0]
        result.append({
            'id': site_id,
            'name': site_info[site_id]['name'],
            'url': site_info[site_id]['url'],
            'similarity': rec[1]
        })

    return result

def load_url_names_from_database(df):
    url_names = {}
    try:
        for index, row in df.iterrows():
            url_names[int(row['id'])] = row['name']
    except FileNotFoundError:
        print("Arquivo não encontrado data_url_DATABSE")
    except Exception as e:
        print("Erro ao ler o arquivo data_url_DATABASE:", str(e))  # Imprime o erro específico
    return url_names


# ----------------------------------- ROTAS --------------------------------------#


@app.route('/')
def index():
    email = session.get('email')
    if email:
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
        name = user_info.get('name')
        
        if not email:
            raise ValueError("Email not found in user_info", user_info)
        
        session['email'] = email
        session['name'] = name

        # Verifica se o usuário já existe no banco de dados
        user = tbl_user.query.filter_by(email=email).first()
        if not user:
                new_user = tbl_user(email=email, name=name)
                db.session.add(new_user)
                db.session.commit()
                user = new_user

        session['user_id'] = user.id
        
        insert_initial_user_favs(user.id)

        print('Usuário autenticado com sucesso:', email)
        return redirect(url_for('dashboard'))
    
    except Exception as e:
        print('Erro durante a autorização:', e)
    
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    email = session.get('email')
    name = session.get('name')
    if email:
        user_id = session.get('user_id')
        
        # Consulta ao banco de dados para recuperar os sites favoritos do usuário atual
        user_news = db.session.query(tbl_user_fav, tbl_sites).join(tbl_sites, tbl_user_fav.site_id == tbl_sites.id
                    ).filter(
                        tbl_user_fav.user_id == user_id
                    ).order_by(func.random()).limit(5).all()
        
        urls = []
        for fav, site in user_news:
            urls.append({
                'id': fav.id,
                'user_id': fav.user_id,
                'name': site.name,
                'url': site.url,
                'rate': fav.rate
            })

        recommend_sites = recommend_sites_for_user()

        # Seleciona novamente os dados das URLs para este usuário
        engine = create_engine(os.getenv('POSTGRES_LOGIN'))
        query = "SELECT id, name, url, description FROM url_data"
        url_data = pd.read_sql(query, con=engine)

        url_names = load_url_names_from_database(url_data)

        return render_template('dashboard.html', name=name, email=email, urls=urls, recommend_sites=recommend_sites, url_names=url_names)
    else:
        return redirect('/')



@app.route('/update_rate', methods=['POST'])
def update_rate():
    data = request.get_json()
    user_id = data.get('user_id')
    url = data.get('url')
    rate = data.get('rate')

    # Consulta ao banco de dados para encontrar a notícia correspondente
    news_item = tbl_user_fav.query.filter_by(user_id=user_id, url=url).first()
    
    if news_item:
        # Atualiza o valor de 'rate' no banco de dados
        news_item.rate = rate
        db.session.commit()
        return 'Rate atualizado com sucesso!'
    else:
        return 'Notícia não encontrada para o usuário especificado.', 404

    return 'Método inválido.', 400



# ----------------- Inicializa a aplicação no server

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)