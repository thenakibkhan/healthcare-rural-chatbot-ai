from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user, UserMixin
from database import create_user, get_user_by_email, get_user_by_id, verify_password

auth_bp = Blueprint('auth', __name__)

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not name or not email or not password:
        return jsonify({'error': 'Missing fields'}), 400
        
    user_id = create_user(name, email, password)
    if user_id:
        return jsonify({'message': 'User registered successfully', 'success': True}), 201
    else:
        return jsonify({'error': 'Email already exists', 'success': False}), 409

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    db_user = get_user_by_email(email)
    
    if db_user and verify_password(db_user['password'], password):
        user = User(id=db_user['id'], name=db_user['name'], email=db_user['email'])
        login_user(user, remember=True)
        return jsonify({'message': 'Login successful', 'user': {'name': user.name}, 'success': True})
    
    return jsonify({'error': 'Invalid credentials', 'success': False}), 401
    
@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully', 'success': True})

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    if current_user.is_authenticated:
        return jsonify({'authenticated': True, 'user': {'name': current_user.name, 'email': current_user.email}})
    return jsonify({'authenticated': False})
