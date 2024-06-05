# googleAuth.py

from flask import redirect, url_for, session, render_template, request
from authlib.integrations.flask_client import OAuth

oauth = OAuth()

google = oauth.register(
    name='google',
    client_id='213167038682-1ch7jaaqftacmkoc6c127qim1te6kjoh.apps.googleusercontent.com',
    client_secret='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',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid profile email'},
)

def init_app(flask_app):
    global app
    app = flask_app
    oauth.init_app(app)

def login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

def logout():
    session.pop('email', None)
    return redirect('/')

def authorize():
    try:
        token = google.authorize_access_token()
        user_info_resp = google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
        user_info = user_info_resp.json()
        email = user_info.get('email')
        session['email'] = email
        print('Usuário autenticado com sucesso:', email)
        return redirect(url_for('dashboard'))
    except Exception as e:
        print('Erro durante a autorização:', e)
        return redirect('/')
