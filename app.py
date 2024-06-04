from flask import Flask, redirect, url_for, session, render_template
from authlib.integrations.flask_client import OAuth

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

@app.route('/')
def index():
    email = session.get('email')
    if email:
        return redirect(url_for('dashboard'))  # Se o usuário estiver autenticado, redirecionar para a dashboard
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
        session['email'] = user_info.get('email')
        print('Usuário autenticado com sucesso:', session['email'])
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

if __name__ == '__main__':
    app.run(debug=True)
