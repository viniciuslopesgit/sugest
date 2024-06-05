from flask import jsonify
from flask import Flask, redirect, url_for, session, render_template, request
from authlib.integrations.flask_client import OAuth
import pandas as pd
import random
from flask_sqlalchemy import SQLAlchemy

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

# Modelo de dados do banco de dados
class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50))
    url = db.Column(db.String(200))
    rate = db.Column(db.Integer)

    def __init__(self, user_id, url, rate):
        self.user_id = user_id
        self.url = url
        self.rate = rate

    def update_rate(self):
        # Incrementa o valor de 'rate' em 1
        self.rate += 1

# Função para gerar URLs de notícias e inserir no banco de dados
def generate_news_urls(user_id):
    existing_urls_count = News.query.filter_by(user_id=user_id).count()

    if existing_urls_count == 5:
        # Já existem cinco URLs, não é necessário adicionar mais
        return []
    elif existing_urls_count < 5:
        # Precisamos adicionar mais URLs até que existam cinco no total
        news_data = pd.read_csv('data/news.csv')
        selected_urls = random.sample(news_data['url'].tolist(), 5 - existing_urls_count)

        news_list = []
        for url in selected_urls:
            rate = 0
            new_url = News(user_id=user_id, url=url, rate=rate)
            db.session.add(new_url)
            news_list.append({'user_id': user_id, 'url': url, 'rate': rate})
        
        db.session.commit()

        return news_list



# Rotas da sua aplicação
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
        session['email'] = email
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
    if email:
        user_id = session.get('user_id')
        
        # Gere URLs de notícias se necessário
        generate_news_urls(user_id)
        
        # Consulta ao banco de dados para recuperar as notícias do usuário atual
        user_news = News.query.filter_by(user_id=user_id).all()
        urls = []
        for news in user_news:
            urls.append({
                'user_id': news.user_id,
                'url': news.url,
                'rate': news.rate
            })
        return render_template('dashboard.html', email=email, urls=urls)
    else:
        return redirect('/')


@app.route('/update_rate', methods=['POST'])
def update_rate():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        url = request.form.get('url')
        
        # Consulta ao banco de dados para encontrar a notícia correspondente
        news_item = News.query.filter_by(user_id=user_id, url=url).first()
        
        if news_item:
            # Atualiza o valor de 'rate' no banco de dados
            news_item.rate += 1
            db.session.commit()
            
            return 'Rate atualizado com sucesso!'
        else:
            return 'Notícia não encontrada para o usuário especificado.'

    return 'Método inválido.'




if __name__ == '__main__':
    app.run(debug=True)
