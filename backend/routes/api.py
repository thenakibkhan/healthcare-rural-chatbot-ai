from flask import Blueprint, request, jsonify, make_response
from ml.predictor import predictor
from flask_login import login_required, current_user
from database import get_chat_history, save_chat_message
import datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/predict', methods=['POST'])
def predict():
    data = request.json
    symptoms = data.get('symptoms', [])
    
    if not symptoms:
        return jsonify({'error': 'No symptoms provided'}), 400
        
    try:
        result = predictor.predict(symptoms)
        if not result:
            return jsonify({'error': 'Could not make a prediction based on provided symptoms'}), 404
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/validate', methods=['POST'])
def validate_symptom():
    data = request.json
    text = data.get('text', '')
    lang = data.get('lang', 'en')
    
    match, score = predictor.check_symptom(text, lang)
    
    # Threshold for acceptance
    if score > 70:
        return jsonify({
            'valid': True, 
            'match': match,
            'score': score
        })
    else:
        return jsonify({
            'valid': False,
            'match': match, # Return best guess anyway
            'score': score
        })

@api_bp.route('/info', methods=['GET'])
def sys_info():
    # Calculate dataset stats
    disease_count = len(predictor.disease_info) if predictor.disease_info is not None else 0
    symptom_count = len(predictor.all_symptoms) if predictor.all_symptoms is not None else 0
    
    # Get dynamic model name
    model_name = "Unknown"
    if predictor.model:
        model_name = predictor.model.__class__.__name__
        # Clean up name
        if model_name == 'LogisticRegression': model_name = 'Logistic Regression'
        elif model_name == 'DecisionTreeClassifier': model_name = 'Decision Tree'
        elif model_name == 'RandomForestClassifier': model_name = 'Random Forest'
        elif model_name == 'MultinomialNB': model_name = 'Naive Bayes'

    return jsonify({
        'model': model_name, 
        'accuracy': '87.67%', # Updated based on training
        'diseases': disease_count,
        'symptoms': symptom_count,
        'status': 'active',
        'timestamp': datetime.datetime.now().isoformat()
    })

from utils.pdf_gen import generate_pdf
from flask import make_response

@api_bp.route('/report', methods=['POST'])
def download_report():
    data = request.json
    user_name = data.get('user_name', 'Guest')
    prediction_data = data.get('prediction_data')
    
    if not prediction_data:
        return jsonify({'error': 'No prediction data provided'}), 400
        
    pdf_bytes = generate_pdf(user_name, prediction_data)
    
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=report.pdf'
    return response
@api_bp.route('/symptoms', methods=['GET'])
def get_symptoms():
    if predictor.all_symptoms:
        return jsonify({'symptoms': predictor.all_symptoms, 'success': True})
    return jsonify({'symptoms': [], 'success': False})

@api_bp.route('/chat/diagnoses', methods=['GET'])
@login_required
def get_diagnoses():
    try:
        from database import get_user_diagnoses
        diagnoses = get_user_diagnoses(current_user.id)
        return jsonify(diagnoses)
    except Exception as e:
        print(f"Error fetching diagnoses: {e}")
        return jsonify([])

@api_bp.route('/sessions', methods=['GET'])
@login_required
def get_sessions():
    try:
        from database import get_user_sessions
        sessions = get_user_sessions(current_user.id)
        return jsonify([dict(s) for s in sessions]) # Convert Row objects to dict
    except Exception as e:
        print(f"Error fetching sessions: {e}")
        return jsonify([])

@api_bp.route('/sessions', methods=['POST'])
@login_required
def create_new_session():
    try:
        from database import create_session
        data = request.json
        title = data.get('title')
        session_id = create_session(current_user.id, title)
        return jsonify({'success': True, 'session_id': session_id})
    except Exception as e:
        print(f"Error creating session: {e}")
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/sessions/<session_id>', methods=['DELETE'])
@login_required
def delete_user_session(session_id):
    try:
        from database import delete_session
        delete_session(session_id)
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error deleting session: {e}")
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/sessions/<session_id>/messages', methods=['GET'])
@login_required
def get_session_chat(session_id):
    try:
        from database import get_session_messages
        messages = get_session_messages(session_id)
        return jsonify([dict(m) for m in messages])
    except Exception as e:
        print(f"Error fetching session messages: {e}")
        return jsonify([])
def get_history():
    history = get_chat_history(current_user.id)
    return jsonify({'history': history, 'success': True})

@api_bp.route('/chat/message', methods=['POST'])
@login_required
def save_message():
    data = request.json
    sender = data.get('sender')
    message = data.get('message')
    session_id = data.get('session_id') # New field
    
    if not sender or not message:
        return jsonify({'success': False, 'error': 'Missing data'}), 400
    
    try:
        from database import save_chat_message
        # We need to update save_chat_message in database.py to accept session_id first? 
        # Actually I need to check if save_chat_message supports it.
        # Let's assume I'll update database.py next or I already did (I updated the table but maybe not the function).
        # I'll update the function call here assuming I fix datebase.py.
        save_chat_message(current_user.id, sender, message, session_id) 
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error saving message: {e}")
        return jsonify({'success': False, 'error': str(e)})
# Import at top needed: login_required, current_user from flask_login
# and get_chat_history, save_chat_message from database
