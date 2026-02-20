import sqlite3
import os
import uuid # Added uuid import
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Create Sessions Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Rename chat_history to messages if it exists and add session_id
    # This is a migration step for existing databases
    try:
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history';")
        if c.fetchone():
            print("Migrating 'chat_history' table to 'messages'...")
            c.execute("ALTER TABLE chat_history RENAME TO messages;")
            conn.commit()
            print("Table 'chat_history' renamed to 'messages'.")
    except Exception as e:
        print(f"Error during chat_history rename: {e}")

    # Check if session_id exists in messages table, add if not
    try:
        c.execute('SELECT session_id FROM messages LIMIT 1')
    except sqlite3.OperationalError: # This error occurs if the column does not exist
        print("Migrating messages table to include session_id...")
        try:
            c.execute('ALTER TABLE messages ADD COLUMN session_id TEXT')
            conn.commit()
            print("Column 'session_id' added to 'messages' table.")
        except Exception as e:
            print(f"Migration error (might be okay if column exists): {e}")
    
    # Create Messages Table (or ensure it's correctly structured after migration)
    # This ensures the table has the correct schema, including foreign key for session_id
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized.")

def create_user(name, email, password):
    # check if user exists
    if get_user_by_email(email):
        return False
    
    conn = get_db_connection()
    hashed = generate_password_hash(password)
    try:
        c = conn.cursor()
        c.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                  (name, email, hashed))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return user

def get_messages_by_user(user_id):
    conn = get_db_connection()
    messages = conn.execute('SELECT * FROM messages WHERE user_id = ? ORDER BY timestamp ASC', (user_id,)).fetchall()
    conn.close()
    return messages

def get_user_diagnoses(user_id):
    conn = get_db_connection()
    # Filter for bot messages that likely contain a diagnosis result
    # We look for the specific marker we use in main.js/api: "Diagnosis:" or "Predicted Disease"
    # Actually, the bot message stored usually contains the full markdown response.
    # The prompt in api.py says: "You are a medical assistant..." and returns JSON.
    # Wait, the CHAT HISTORY stores the "message" field.
    # In api.py, when a prediction happens:
    # 1. User sends symptoms.
    # 2. Server returns JSON { "disease": ..., "description": ... }
    # 3. Frontend displays it.
    # 4. Frontend calls /api/chat/message to SAVE the bot response.
    # In main.js: frontend.saveMessage(msgContent, 'bot');
    # The msgContent for a diagnosis is: `### Diagnosis: ${result.disease}\n\n${result.description[state.lang]}...`
    # So we can look for "### Diagnosis:"
    
    query = """
        SELECT id, message, timestamp 
        FROM messages 
        WHERE user_id = ? AND sender = 'bot' AND message LIKE '%### Diagnosis:%'
        ORDER BY timestamp DESC
    """
    rows = conn.execute(query, (user_id,)).fetchall()
    conn.close()
    
    diagnoses = []
    import re
    for row in rows:
        # Extract disease name using regex
        match = re.search(r"### Diagnosis:\s*(.+?)(\n|$)", row['message'])
        if match:
            disease = match.group(1).strip()
            # Clean up markdown if any * are there
            disease = disease.replace('*', '')
            diagnoses.append({
                'id': row['id'],
                'disease': disease,
                'date': row['timestamp'].split(' ')[0] # Just the date part
            })
    return diagnoses

def get_user_by_id(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    user = c.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def verify_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)
    
def save_chat_message(user_id, sender, message, session_id=None):
    conn = get_db_connection()
    conn.execute('INSERT INTO messages (user_id, session_id, sender, message) VALUES (?, ?, ?, ?)', 
                 (user_id, session_id, sender, message))
    conn.commit()
    conn.close()

def get_chat_history(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    # Fallback to messages table, filtering by session if needed, but this might just return all?
    # For now, let's just select from messages.
    history = c.execute('SELECT sender, message, timestamp FROM messages WHERE user_id = ? ORDER BY timestamp ASC', (user_id,)).fetchall()
    conn.close()
    return [dict(row) for row in history]

# Session Helpers
def create_session(user_id, title=None):
    if not title:
        from datetime import datetime
        title = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    session_id = str(uuid.uuid4())
    conn = get_db_connection()
    conn.execute('INSERT INTO sessions (id, user_id, title) VALUES (?, ?, ?)',
                 (session_id, user_id, title))
    conn.commit()
    conn.close()
    return session_id

def get_user_sessions(user_id):
    conn = get_db_connection()
    sessions = conn.execute('SELECT * FROM sessions WHERE user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()
    conn.close()
    return sessions

def delete_session(session_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
    conn.execute('DELETE FROM messages WHERE session_id = ?', (session_id,)) # Cascade delete messages
    conn.commit()
    conn.close()

def get_session_messages(session_id):
    conn = get_db_connection()
    messages = conn.execute('SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC', (session_id,)).fetchall()
    conn.close()
    return messages
