import pandas as pd
import random
from werkzeug.security import generate_password_hash
from datetime import datetime
from flask import jsonify
from flask import Flask, redirect, url_for, session, render_template, request, jsonify
from authlib.integrations.flask_client import OAuth
from flask_sqlalchemy import SQLAlchemy
from bs4 import BeautifulSoup
app = Flask(__name__)

app.secret_key = 'seu_segredo'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:mabsam@localhost/db_users'

db = SQLAlchemy(app)

app.config['GOOGLE_CLIENT_ID'] = '213167038682-1ch7jaaqftacmkoc6c127qim1te6kjoh.apps.googleusercontent.com'
app.config['GOOGLE_CLIENT_SECRET'] = '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'

oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id='213167038682-1ch7jaaqftacmkoc6c127qim1te6kjoh.apps.googleusercontent.com',
    client_secret='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',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid profile email'},
)


# -------------------------------- FUNÇÕES --------------------------------------

# Criando login de usuário com a conta Google
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255))
    name = db.Column(db.String(255))

    def __init__(self, email, name, password=None):
        self.email = email
        self.name = name
        if password:
            self.password = generate_password_hash(password)

# Sistema de Favorito
class User_fav(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50))
    url = db.Column(db.String(200))
    rate = db.Column(db.Integer)

    def __init__(self, id, user_id, url, rate):
        self.id = id
        self.user_id = user_id
        self.url = url
        self.rate = rate

    def update_rate(self):
        self.rate += 1

def generate_news_urls(user_id):
    existing_urls_count = User_fav.query.filter_by(user_id=user_id).count()

    if existing_urls_count == 5:
        return []
    elif existing_urls_count < 5:
        news_data = pd.read_csv('data/url_data.csv')

        existing_urls = [fav.url for fav in User_fav.query.filter_by(user_id=user_id).all()]
        available_urls = news_data[~news_data['url'].isin(existing_urls)]

        selected_urls = random.sample(available_urls.to_dict(orient='records'), 5 - existing_urls_count)

        news_list = []
        for url_data in selected_urls:
            id = url_data['id']
            url = url_data['url']
            rate = 0
            new_url = User_fav(id=id, user_id=user_id, url=url, rate=rate)
            db.session.add(new_url)
            news_list.append({'id': id, 'user_id': user_id, 'url': url, 'rate': rate})
        
        db.session.commit()

        return news_list

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
    rated_urls = User_fav.query.filter_by(user_id=user_id, rate=1).all()
    rated_ids = [url.id for url in rated_urls]

    if not rated_ids:
        print("Nenhum site está favoritado")
        return "Nenhum site está favoritado"
    
    url_data = pd.read_csv('data/url_data.csv')
    rated_sites_data = url_data[url_data['id'].isin(rated_ids)]

    if rated_sites_data.empty:
        print("Nenhum dado correspondente encontrado no arquivo .csv")
        return "Nenhum dado correspondente encontrado no arquivo .csv"
    
    rated_keywords = set()
    for keywords in rated_sites_data['keywords']:
        if isinstance(keywords, str):
            rated_keywords.update(keywords.split(','))

    recommendations = []
    site_info = {}
    for index, row in url_data.iterrows():
        site_info[row['id']] = {'name': row['name'], 'url': row['url']}
        if row['id'] not in rated_ids:
            if isinstance(row['keywords'], str):
                site_keywords = set(row['keywords'].split(','))
                similarity = jaccard_similarity(rated_keywords, site_keywords)
                recommendations.append((row['id'], similarity))

    # Ordenar as recomendações pela maior similaridade
    recommendations.sort(key=lambda x: x[1], reverse=True)

    top_recommendations = recommendations[:100]

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

def load_url_names_from_csv():
    url_names = {}
    try:
        df = pd.read_csv('data/url_data.csv')

        for index, row in df.iterrows():
            url_names[int(row['id'])] = row['name']
    except FileNotFoundError:
        print("Arquivo data_url.csv não encontrado")
    except Exception as e:
        print("Erro ao ler o arquivo data.url.csv")
    return url_names

def generate_random_color():
    # Gera uma cor aleatória em formato hexadecimal
    color = '#{:06x}'.format(random.randint(0, 0xFFFFFF))
    return color


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
        user = User.query.filter_by(email=email).first()
        if not user:
                new_user = User(email=email, name=name)
                db.session.add(new_user)
                db.session.commit()
        
        # Simulação de um user_id
        session['user_id'] = email.split('@')[0]
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
        
        # Gere URLs de notícias se necessário
        generate_news_urls(user_id)
        
        # Consulta ao banco de dados para recuperar as notícias do usuário atual
        user_news = User_fav.query.filter_by(user_id=user_id).all()
        urls = []
        for news in user_news:
            urls.append({
                'id': news.id,
                'user_id': news.user_id,
                'url': news.url,
                'rate': news.rate
            })
        
        recommend_sites = recommend_sites_for_user()
        print(recommend_sites_for_user())

        url_names = load_url_names_from_csv()

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
    news_item = User_fav.query.filter_by(user_id=user_id, url=url).first()
    
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
