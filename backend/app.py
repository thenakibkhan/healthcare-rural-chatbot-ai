from flask import Flask, render_template, url_for, redirect, flash
from flask_cors import CORS
from flask_login import LoginManager, login_user
from authlib.integrations.flask_client import OAuth
import os
from config import Config
from routes.auth import auth_bp, User
from routes.api import api_bp
from database import init_db, get_user_by_id, get_user_by_email, create_user

app = Flask(__name__, 
            template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates')),
            static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), 'static')))
app.config.from_object(Config)

# Initialize DB
init_db()

CORS(app)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    db_user = get_user_by_id(user_id)
    if db_user:
        return User(id=db_user['id'], name=db_user['name'], email=db_user['email'])
    return None 

# OAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openid email scope
    client_kwargs={'scope': 'openid email profile'},
)

app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/auth')

# Frontend Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/tech')
def tech():
    return render_template('tech.html')

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/features')
def features():
    return render_template('features.html')

# Google Auth Routes
@app.route('/login/google')
def google_login():
    if not os.environ.get('GOOGLE_CLIENT_ID') or not os.environ.get('GOOGLE_CLIENT_SECRET'):
        return render_template('login.html', error="Google Login not configured (Missing Client ID/Secret)")
    redirect_uri = url_for('google_auth', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def google_auth():
    try:
        token = google.authorize_access_token()
        user_info = google.parse_id_token(token, nonce=None)
        
        # Check if user exists
        email = user_info['email']
        name = user_info['name']
        
        db_user = get_user_by_email(email)
        if not db_user:
            # Create user with random password (they can't login with password unless they reset it, which is fine)
            import secrets
            random_pw = secrets.token_urlsafe(16)
            create_user(name, email, random_pw)
            db_user = get_user_by_email(email)
            
        # Login
        user = User(id=db_user['id'], name=db_user['name'], email=db_user['email'])
        login_user(user, remember=True)
        return redirect('/chat')
    except Exception as e:
        print(f"Google Auth Error: {e}")
        return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
    # Reload trigger
