# blueprints/auth/routes.py
import time
import sqlite3
import jwt
from functools import wraps
from flask import Blueprint, request, jsonify, make_response, current_app, g
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection

auth_bp = Blueprint('auth', __name__)

def jwt_required(f):
    """Decorator to protect routes with JWT stored in an HttpOnly cookie."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Match cookie name token key
        token = request.cookies.get('session_token') or request.cookies.get('token')
        
        if not token:
            return jsonify({"error": "Authentication token missing"}), 401
        
        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=["HS256"])
            g.current_user_id = data["user_id"]
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return jsonify({"error": "Invalid or expired session token"}), 401
            
        # PASS g.current_user_id as the first positional argument to match your routes!
        return f(g.current_user_id, *args, **kwargs)
    return decorated


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()

    if not all([username, password, name, email]):
        return jsonify({"error": "All parameter metadata blocks are required"}), 400

    hashed_password = generate_password_hash(password)
    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, name, email) VALUES (?, ?, ?, ?)",
            (username, hashed_password, name, email)
        )
        db.commit()
        return jsonify({"status": "success", "message": "Identity instance mapped safely"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username or routing email already registered"}), 409

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({"error": "Missing security verification arguments"}), 400

    db = get_db_connection()
    cursor = db.cursor()
    user = cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Invalid security credentials"}), 401

    # Dynamically fetch secret from app configuration context to sign token
    token = jwt.encode(
        {"user_id": user['id'], "exp": time.time() + (7 * 24 * 3600)},
        current_app.config['JWT_SECRET'],
        algorithm="HS256"
    )

    response = make_response(jsonify({"status": "success", "message": "Handshake complete"}))
    
    # Pack securely inside the user cookie context layer
    response.set_cookie(
        'session_token',
        token,
        httponly=current_app.config.get('SESSION_COOKIE_HTTPONLY', True),
        secure=current_app.config.get('SESSION_COOKIE_SECURE', False), # False for local Termux network testing
        samesite='Lax',
        max_age=7 * 24 * 3600
    )
    
    return response

@auth_bp.route('/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({"status": "success", "message": "Session context dropped"}))
    response.set_cookie('session_token', '', expires=0)
    return response
