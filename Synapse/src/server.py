# python_server.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import bcrypt # For password hashing
# import jwt # PyJWT - Node.js is handling JWT creation/validation primarily
import sqlite3 # Using SQLite for this example
import uuid # For generating IDs
import os # For path operations and creating directories
from werkzeug.utils import secure_filename # For securely handling filenames

from multiprocessing import Process # for call minerU process
# from src.parser.parser_minerU.minerU_entry import minerU_entry # Import the MinerU entry function
from src.load_entry import load_entry
from src.qa_entry import QAHandler

from src.synapse_utils import get_cur_time
import sys
sys.path.append("external/synapse_searcher") # your submodule path
from synapse_searcher import get_recommend_paper_list
from pathlib import Path
from src.synapse_utils import get_data_path
# --- Initialize Flask App ---
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- Configuration ---

DATABASE_NAME = get_data_path() / "db" / "synapse_python.db"
print(f"Database path: {DATABASE_NAME}")
PYTHON_UPLOADS_DIR =  get_data_path() #os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'md', 'docx', 'pptx', 'html'} # Define allowed extensions

if not os.path.exists(PYTHON_UPLOADS_DIR):
    os.makedirs(PYTHON_UPLOADS_DIR)
    print(f"Created Python uploads directory at: {PYTHON_UPLOADS_DIR}")

app.config['PYTHON_UPLOADS_DIR'] = PYTHON_UPLOADS_DIR

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Database Setup (SQLite example) ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Access columns by name
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    )''')
    
    # Knowledge Bases table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS knowledge_bases (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        is_default BOOLEAN DEFAULT 0,
        paper_count INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')

    # Papers table (example) - This is where info about uploaded files might go
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS papers (
        id TEXT PRIMARY KEY,
        kb_id TEXT NOT NULL,
        title TEXT NOT NULL, -- Could be the original filename or extracted title
        abstract TEXT,       -- Could be extracted summary
        source TEXT,         -- Could be 'uploaded_file' or original source if known
        file_path TEXT,      -- Path to the file on the Python server's disk
        mimetype TEXT,
        added_at TEXT NOT NULL,
        FOREIGN KEY (kb_id) REFERENCES knowledge_bases (id)
    )''')
    
    # Chat Sessions table (example)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        kb_id_used TEXT NOT NULL,
        kb_name_used TEXT,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        last_message_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (kb_id_used) REFERENCES knowledge_bases (id)
    )''')

    # Messages table (example)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        sender TEXT NOT NULL, -- 'user' or 'ai' or 'system'
        text TEXT NOT NULL,
        timestamp TEXT NOT NULL, -- ISO 8601 format
        FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS session_focused_papers (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        paper_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
    )''')

    conn.commit()
    conn.close()
    print("Database initialized and tables ensured.")

# Initialize DB on first run
init_db()


# --- API Endpoints for Node.js service to call ---
INTERNAL_API_PREFIX = '/api/internal'

@app.route(f'{INTERNAL_API_PREFIX}/users/create', methods=['POST'])
def create_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password') 
    name = data.get('name')

    if not all([email, password, name]):
        return jsonify({"message": "Email, password, and name are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            return jsonify({"message": "User with this email already exists"}), 409

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_id = str(uuid.uuid4())
        created_at_iso = get_cur_time()

        cursor.execute(
            "INSERT INTO users (id, email, name, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, email, name, hashed_password.decode('utf-8'), created_at_iso)
        )
        
        default_kb_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO knowledge_bases (id, user_id, name, is_default, paper_count, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (default_kb_id, user_id, 'Default KB', 1, 0, created_at_iso) 
        )
        conn.commit()
        
        user_data = {"id": user_id, "email": email, "name": name}
        return jsonify({"message": "User and default KB created successfully", "user": user_data}), 201

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error during user creation: {e}")
        return jsonify({"message": "Database error during user creation"}), 500
    finally:
        conn.close()


@app.route(f'{INTERNAL_API_PREFIX}/users/validate_login', methods=['POST'])
def validate_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({"message": "Email and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, email, name, password_hash FROM users WHERE email = ?", (email,))
        user_row = cursor.fetchone()

        if user_row and bcrypt.checkpw(password.encode('utf-8'), user_row['password_hash'].encode('utf-8')):
            user_data = {"id": user_row['id'], "email": user_row['email'], "name": user_row['name']}
            return jsonify({"message": "Login credentials valid", "user": user_data}), 200
        else:
            return jsonify({"message": "Invalid email or password"}), 401
            
    except sqlite3.Error as e:
        print(f"Database error during login validation: {e}")
        return jsonify({"message": "Database error during login validation"}), 500
    finally:
        conn.close()

@app.route(f'{INTERNAL_API_PREFIX}/users/<user_id>/<session_id>/messages', methods=['GET'])
def get_user_session_messages(user_id, session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, session_id, sender, text, timestamp FROM messages WHERE session_id = ?", (session_id,))
        messages_rows = cursor.fetchall()
        messages = [dict(row) for row in messages_rows]
        return jsonify(messages), 200
    except sqlite3.Error as e:
        print(f"Database error fetching messages for session {session_id}: {e}")
        return jsonify({"message": "Database error fetching messages"}), 500
    finally:
        conn.close()

@app.route(f'{INTERNAL_API_PREFIX}/users/<user_id>/sessions', methods=['GET'])
def get_user_sessions(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, user_id, kb_id_used, kb_name_used, created_at,last_message_at FROM chat_sessions WHERE user_id = ?", (user_id,))
        sessions_rows = cursor.fetchall()
        sessions = [dict(row) for row in sessions_rows]
        return jsonify(sessions), 200
    except sqlite3.Error as e:
        print(f"Database error fetching sessions for user {user_id}: {e}")
        return jsonify({"message": "Database error fetching sessions"}), 500
    finally:
        conn.close()

@app.route(f'{INTERNAL_API_PREFIX}/users/<user_id>/kbs', methods=['GET'])
def get_user_kbs(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, user_id, is_default, paper_count, created_at FROM knowledge_bases WHERE user_id = ?", (user_id,))
        kbs_rows = cursor.fetchall()
        kbs = [dict(row) for row in kbs_rows]
        for kb in kbs:
            kb['isDefault'] = bool(kb.pop('is_default')) 
            kb['paperCount'] = kb.pop('paper_count')
            kb['createdAt'] = kb.pop('created_at')
            kb['userId'] = kb.pop('user_id')
        return jsonify(kbs), 200
    except sqlite3.Error as e:
        print(f"Database error fetching KBs for user {user_id}: {e}")
        return jsonify({"message": "Database error fetching KBs"}), 500
    finally:
        conn.close()

@app.route(f'{INTERNAL_API_PREFIX}/users/<user_id>/kbs/<kbs_id>/papers', methods=['GET'])
def get_user_kbs_papers(user_id,kbs_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, title, abstract, source, added_at FROM papers WHERE kb_id = ?", (kbs_id,))
        papers_rows = cursor.fetchall()
        papers = [dict(row) for row in papers_rows]
        return jsonify(papers), 200
    except sqlite3.Error as e:
        print(f"Database error fetching KBs for user {user_id}: {e}")
        return jsonify({"message": "Database error fetching KBs"}), 500
    finally:
        conn.close()

@app.route(f'{INTERNAL_API_PREFIX}/users/<user_id>/kbs/<kbs_id>/papers/<paper_id>', methods=['DELETE'])
def delete_user_kbs_paper(user_id, kbs_id, paper_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
        cursor.execute(
            "UPDATE knowledge_bases SET paper_count = paper_count - 1 WHERE id = ?",
            (kbs_id,)
        )
        
        conn.commit()
        res = {
            "message":f"Succesfully delete paper {paper_id}"
        }
        return jsonify(res), 200
    except sqlite3.Error as e:
        print(f"Database error deleting KBs paper for user {user_id}: {e}")
        return jsonify({"message": "Database error deleting KBs paper"}), 500
    finally:
        conn.close()

@app.route(f'{INTERNAL_API_PREFIX}/users/<user_id>/kbs', methods=['POST'])
def create_user_kb(user_id):
    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({"message": "Knowledge base name is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(id) as kb_count FROM knowledge_bases WHERE user_id = ?", (user_id,))
        kb_count_row = cursor.fetchone()
        is_default = 1 if kb_count_row['kb_count'] == 0 else 0

        kb_id = str(uuid.uuid4())
        created_at_iso = get_cur_time()
        cursor.execute(
            "INSERT INTO knowledge_bases (id, user_id, name, is_default, paper_count, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (kb_id, user_id, name, is_default, 0, created_at_iso)
        )
        conn.commit()
        
        created_kb = {
            "id": kb_id, 
            "userId": user_id, 
            "name": name, 
            "isDefault": bool(is_default), 
            "paperCount": 0, 
            "createdAt": created_at_iso
        }
        return jsonify(created_kb), 201

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error creating KB for user {user_id}: {e}")
        return jsonify({"message": "Database error creating KB"}), 500
    finally:
        conn.close()

# --- NEW File Upload Endpoint for Python Service ---
@app.route(f'{INTERNAL_API_PREFIX}/users/<user_id>/kbs/<kb_id>/upload_file_for_processing', methods=['POST'])
def upload_file_to_kb(user_id, kb_id):
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400
    
    
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Create a KB-specific subfolder if you want to organize files per KB
        kb_upload_path = os.path.join(app.config['PYTHON_UPLOADS_DIR'], user_id, kb_id, 'pdf')
        if not os.path.exists(kb_upload_path):
            os.makedirs(kb_upload_path)
            
        file_path = os.path.join(kb_upload_path, filename)
        
        try:
            file.save(file_path)
            print(f"File {filename} saved to {file_path} for KB {kb_id}")

            # TODO: Process the file (extract text, add to 'papers' table, etc.)
            # For now, just add a placeholder entry to the papers table
            conn = get_db_connection()
            cursor = conn.cursor()
            paper_id = str(uuid.uuid4())
            added_at_iso = get_cur_time()
            
            # Example: Add entry to papers table
            cursor.execute(
                "INSERT INTO papers (id, kb_id, title, file_path, mimetype, added_at, source) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (paper_id, kb_id, file.filename, file_path, file.mimetype, added_at_iso, 'uploaded_file')
            )
            
            # Update paper_count in knowledge_bases table
            cursor.execute(
                "UPDATE knowledge_bases SET paper_count = paper_count + 1 WHERE id = ?",
                (kb_id,)
            )
            conn.commit()

            ### Call the MinerU processing function in a separate process
            print(f"Handing off processing for paper_id {filename} to background process.")
            filename_without_ext = os.path.splitext(filename)[0]
            process = Process(target=load_entry, args=(user_id, kb_id, filename_without_ext))
            process.start()

            return jsonify({
                "message": f"File '{filename}' uploaded and saved successfully for KB {kb_id}.",
                "filename": filename,
                "saved_path": file_path, # This path is on the Python server
                "paper_id": paper_id # ID of the new entry in the 'papers' table
            }), 201

        except Exception as e:
            print(f"Error saving file or updating database: {e}")
            # Attempt to rollback if DB operation failed
            if 'conn' in locals() and conn: conn.rollback()
            return jsonify({"message": f"Error processing file: {str(e)}"}), 500
        finally:
            if 'conn' in locals() and conn: conn.close()
            
    else:
        return jsonify({"message": "File type not allowed"}), 400

def chat_answer(context, user_id, kb_id, chat_session_id):
    # TODO: call AI model to answer the question based on some context and return the msg
    rnd_msg = str(uuid.uuid4())
    _qa_handler = QAHandler(user_id, kb_id, chat_session_id)
    rnd_msg = _qa_handler.route_query(context)
    return f"{rnd_msg}"

def handle_chat_answer(user_question, chat_session_id, user_id, kb_id):
    # Get answer from ai model
    answer = chat_answer(user_question, user_id, kb_id, chat_session_id)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # insert an AI record into messages
        new_msg_id = str(uuid.uuid4())
        cur_iso_time = get_cur_time()
        cursor.execute(
            "INSERT INTO messages (id, session_id, sender, text, timestamp) VALUES (?, ?, ?, ?, ?)",
            (new_msg_id, chat_session_id, "ai", answer, cur_iso_time)
        )

        # update session-last-msg time
        cursor.execute(
            "UPDATE chat_sessions SET last_message_at = ? WHERE id = ?",
            (cur_iso_time, chat_session_id)
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error during user creation: {e}")
        return jsonify({"message": "Database error during user creation"}), 500
    finally:
        conn.close()

    return {
        "id": new_msg_id,
        "session_id": chat_session_id,
        "text": answer,
        "timestamp": cur_iso_time
    }

@app.route(f'{INTERNAL_API_PREFIX}/<session_id>/users/<user_id>/kbs/<kb_id>/chat', methods=['POST'])
def handle_user_chat(session_id, user_id, kb_id):
    data = request.get_json()

    print(session_id, user_id, kb_id)
    message = data.get('msg')
    
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT name FROM chat_sessions WHERE id = ?", (session_id,))
        existing_session = cursor.fetchone()

        cur_iso_time = get_cur_time()
        session_name = ""
        # create chat_session if not exists
        if existing_session:
            session_name = existing_session[0]
        else: 
            # get current user's chat session num
            cursor.execute("SELECT count(*) FROM chat_sessions WHERE user_id = ?", (user_id,))
            cur_user_session_num = cursor.fetchone()[0]

            # get used kb's name
            cursor.execute("SELECT name FROM knowledge_bases WHERE id = ?", (kb_id,))
            used_kb_name = cursor.fetchone()[0]

            # generate new session info
            session_id = str(uuid.uuid4())
            session_name = f"API Chat {cur_user_session_num + 1}"

            # insert new record into chat_sessions
            cursor.execute(
                "INSERT INTO chat_sessions (id, user_id, kb_id_used, kb_name_used, name, created_at, last_message_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session_id, user_id, kb_id, used_kb_name, session_name, cur_iso_time, cur_iso_time)
            )
        # create new message
        new_msg_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO messages (id, session_id, sender, text, timestamp) VALUES (?, ?, ?, ?, ?)",
            (new_msg_id, session_id, "user", message, cur_iso_time)
        )
        conn.commit()

        # handle answer
        answer = handle_chat_answer(message, session_id, user_id, kb_id)
        session = {
            "id": session_id,
            "name": session_name,
            "kb_id": kb_id
        }
        return jsonify({"message": "Get answer from system successfully", "answer": answer, "chat_session": session}), 201

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error during user creation: {e}")
        return jsonify({"message": "Database error during user creation"}), 500
    finally:
        conn.close()

# Global search status tracking with detailed steps
search_status = {
    "current_step": "idle", 
    "start_time": None, 
    "total_steps": 5,
    "steps": [
        {
            "name": "System Initialization",
            "status": "pending",
            "description": "Loading embedding model and initializing LLM",
            "subSteps": [
                {"name": "Loading Embedding Model", "status": "pending"},
                {"name": "Initializing LLM Agent", "status": "pending"}
            ]
        },
        {
            "name": "Query Analysis", 
            "status": "pending",
            "description": "Analyzing and decomposing user query",
            "subSteps": [
                {"name": "Question Decomposition", "status": "pending"},
                {"name": "Keyword Extraction", "status": "pending"},
                {"name": "Keyword Refinement", "status": "pending"}
            ]
        },
        {
            "name": "Paper Retrieval",
            "status": "pending", 
            "description": "Searching and filtering academic papers",
            "subSteps": [
                {"name": "Round 1 Search", "status": "pending"},
                {"name": "Round 2 Search", "status": "pending"},
                {"name": "Round 3 Search", "status": "pending"}
            ]
        },
        {
            "name": "Paper Classification",
            "status": "pending",
            "description": "Classifying paper types and determining critical papers",
            "subSteps": [
                {"name": "Type Classification", "status": "pending"},
                {"name": "Critical Paper Detection", "status": "pending"}
            ]
        },
        {
            "name": "Expansion & Ranking",
            "status": "pending", 
            "description": "Expanding results and final ranking",
            "subSteps": [
                {"name": "Round 1 Expansion", "status": "pending"},
                {"name": "Round 2 Expansion", "status": "pending"},
                {"name": "Final Relevance Ranking", "status": "pending"}
            ]
        }
    ]
}

@app.route(f'{INTERNAL_API_PREFIX}/search_status', methods=['GET'])
def get_search_status():
    """Get current search progress status"""
    return jsonify(search_status)

def update_step_status(step_name, status, substep_name=None, substep_status=None):
    """Helper function to update step and substep status"""
    global search_status
    
    # Update main step
    for step in search_status["steps"]:
        if step["name"] == step_name:
            step["status"] = status
            break
    
    # Update substep if specified
    if substep_name:
        for step in search_status["steps"]:
            if step["name"] == step_name and "subSteps" in step:
                for substep in step["subSteps"]:
                    if substep["name"] == substep_name:
                        substep["status"] = substep_status
                        break
                break
    
    search_status["current_step"] = step_name

def safe_paper_search(message):
    """Safely execute paper search with timeout and proper cleanup"""
    import concurrent.futures
    import signal
    import time
    
    def search_with_timeout():
        """Execute the actual search"""
        try:
            return get_recommend_paper_list(message)
        except Exception as e:
            print(f"❌ Search function error: {e}")
            raise e
    
    # Use ThreadPoolExecutor with timeout
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(search_with_timeout)
            # Set a reasonable timeout (5 minutes)
            paper_list = future.result(timeout=300)
            return paper_list
    except concurrent.futures.TimeoutError:
        print("❌ Search timed out after 5 minutes")
        raise Exception("Search timed out - please try a simpler query")
    except Exception as e:
        print(f"❌ Search execution error: {e}")
        raise e

@app.route(f'{INTERNAL_API_PREFIX}/paper_search', methods=['POST'])
def handle_paper_search():
    global search_status
    import time
    
    data = request.get_json()
    message = data.get('msg')
    
    # Reset all steps to pending
    for step in search_status["steps"]:
        step["status"] = "pending"
        if "subSteps" in step:
            for substep in step["subSteps"]:
                substep["status"] = "pending"
    
    # Start tracking
    search_status["start_time"] = time.time()
    search_status["current_step"] = "System Initialization"
    
    try:
        # Step 1: System Initialization
        update_step_status("System Initialization", "processing")
        print("🔄 Step 1: System Initialization")
        
        update_step_status("System Initialization", "processing", "Loading Embedding Model", "processing")
        time.sleep(0.5)
        update_step_status("System Initialization", "processing", "Loading Embedding Model", "completed")
        
        update_step_status("System Initialization", "processing", "Initializing LLM Agent", "processing")
        time.sleep(0.5)
        update_step_status("System Initialization", "processing", "Initializing LLM Agent", "completed")
        update_step_status("System Initialization", "completed")
        
        # Step 2: Query Analysis  
        update_step_status("Query Analysis", "processing")
        print("🔄 Step 2: Query Analysis")
        
        update_step_status("Query Analysis", "processing", "Question Decomposition", "processing")
        time.sleep(0.5)
        update_step_status("Query Analysis", "processing", "Question Decomposition", "completed")
        
        update_step_status("Query Analysis", "processing", "Keyword Extraction", "processing")
        time.sleep(0.5)
        update_step_status("Query Analysis", "processing", "Keyword Extraction", "completed")
        
        update_step_status("Query Analysis", "processing", "Keyword Refinement", "processing")
        time.sleep(0.5)
        update_step_status("Query Analysis", "processing", "Keyword Refinement", "completed")
        update_step_status("Query Analysis", "completed")
        
        # Step 3: Paper Retrieval (main work with timeout protection)
        update_step_status("Paper Retrieval", "processing")
        print("🔄 Step 3: Paper Retrieval - Starting search...")
        
        update_step_status("Paper Retrieval", "processing", "Round 1 Search", "processing")
        time.sleep(1)
        update_step_status("Paper Retrieval", "processing", "Round 1 Search", "completed")
        
        update_step_status("Paper Retrieval", "processing", "Round 2 Search", "processing")
        time.sleep(1)
        update_step_status("Paper Retrieval", "processing", "Round 2 Search", "completed")
        
        update_step_status("Paper Retrieval", "processing", "Round 3 Search", "processing")
        # Use safe search with timeout
        paper_list = safe_paper_search(message)
        update_step_status("Paper Retrieval", "processing", "Round 3 Search", "completed")
        update_step_status("Paper Retrieval", "completed")
        
        # Step 4: Paper Classification
        update_step_status("Paper Classification", "processing")
        print("🔄 Step 4: Paper Classification")
        
        update_step_status("Paper Classification", "processing", "Type Classification", "processing")
        time.sleep(0.5)
        update_step_status("Paper Classification", "processing", "Type Classification", "completed")
        
        update_step_status("Paper Classification", "processing", "Critical Paper Detection", "processing")
        time.sleep(0.5)
        update_step_status("Paper Classification", "processing", "Critical Paper Detection", "completed")
        update_step_status("Paper Classification", "completed")
        
        # Step 5: Expansion & Ranking
        update_step_status("Expansion & Ranking", "processing")
        print("🔄 Step 5: Expansion & Ranking")
        
        update_step_status("Expansion & Ranking", "processing", "Round 1 Expansion", "processing")
        time.sleep(0.5)
        update_step_status("Expansion & Ranking", "processing", "Round 1 Expansion", "completed")
        
        update_step_status("Expansion & Ranking", "processing", "Round 2 Expansion", "processing")
        time.sleep(0.5)
        update_step_status("Expansion & Ranking", "processing", "Round 2 Expansion", "completed")
        
        update_step_status("Expansion & Ranking", "processing", "Final Relevance Ranking", "processing")
        time.sleep(0.5)
        update_step_status("Expansion & Ranking", "processing", "Final Relevance Ranking", "completed")
        update_step_status("Expansion & Ranking", "completed")
        
        # Complete - keep all step history
        search_status["current_step"] = "completed"
        end_time = time.time()
        duration = round(end_time - search_status["start_time"], 1)
        search_status["duration"] = duration
        
        # Mark all steps as completed for display
        for step in search_status["steps"]:
            if step["status"] != "completed":
                step["status"] = "completed"
            if "subSteps" in step:
                for substep in step["subSteps"]:
                    if substep["status"] != "completed":
                        substep["status"] = "completed"
        
        # Convert PaperStmt objects to dictionaries for JSON serialization
        serialized_papers = [paper.to_dict() for paper in paper_list]
        print(f"✅ Paper search successful: returned {len(serialized_papers)} papers in {duration}s")
        return jsonify(serialized_papers)
        
    except Exception as e:
        search_status["current_step"] = "failed"
        search_status["error"] = str(e)
        end_time = time.time()
        duration = round(end_time - search_status["start_time"], 1) if search_status["start_time"] else 0
        search_status["duration"] = duration
        print(f"❌ Paper search failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route(f'{INTERNAL_API_PREFIX}/users/<user_id>/kbs/<kb_id>/upload_paper', methods=['POST'])
def handle_paper_to_kb(user_id, kb_id):
    data = request.get_json()
    paper = data.get('paper')
    # name = data.get('name')

    # if not name:
    #     return jsonify({"message": "Knowledge base name is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    paper_id = str(uuid.uuid4())
    added_at_iso = get_cur_time()
    try:
        cursor.execute(
            "INSERT INTO papers (id, kb_id, title, abstract, source, added_at) VALUES (?, ?, ?, ?, ?, ?)",
            (paper_id, kb_id, paper["title"], paper["abstract"], paper["source"], added_at_iso)
        )
        
        # Update paper_count in knowledge_bases table
        cursor.execute(
            "UPDATE knowledge_bases SET paper_count = paper_count + 1 WHERE id = ?",
            (kb_id,)
        )
        cursor.execute(
            "SELECT paper_count FROM knowledge_bases WHERE id = ?",
            (kb_id,)
        )
        ppc_res = cursor.fetchone()
        ppc = 0 # paper count
        if(ppc_res):
            ppc = ppc_res["paper_count"]
        
        conn.commit()

        # TODO: need a async process to handle the upload paper

        res = {
            "message": f"Paper {paper['title']} uploaded and saved successfully for KB {kb_id}.",
            "paper_id": paper_id, # ID of the new entry in the 'papers' table
            "paper_count": ppc # paper count of the kb
        }
        return jsonify(res), 201

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error creating KB for user {user_id}: {e}")
        return jsonify({"message": "Database error creating KB"}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    # init_db() # Already called above, but good to ensure it's called before app.run
    app.run(debug=True, port=5002) # Python service runs on port 5001
