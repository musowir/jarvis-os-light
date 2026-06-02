# ==============================================================================
# SYSTEM INSTANCE CODE BASE : JARVIS CORE FRAMEWORK
# MODULE          : blueprints.auth.routes
# DESCRIPTION     : Handles user authentication, registration, profiles, and cascading deletions.
# COORDINATES     : Layer-3 Backend Logic Blueprint
# SUBSYSTEM       : Authorization & Database Security Gateway
# ==============================================================================

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
    """Terminates session verification handshake by wiping the HTTP-only cookie."""
    response = make_response(jsonify({"status": "success", "message": "Session context dropped"}))
    response.set_cookie('session_token', '', expires=0)
    return response


# ==========================================
# ⚙️ NEW METRICS: USER MANAGEMENT PIPELINE
# ==========================================

@auth_bp.route('/profile', methods=['GET'])
@jwt_required
def get_profile(current_user_id):
    """Fetch profile data fields to populate frontend configuration views."""
    db = get_db_connection()
    cursor = db.cursor()
    
    user = cursor.execute(
        "SELECT name, email FROM users WHERE id = ?", 
        (current_user_id,)
    ).fetchone()
    
    if not user:
        return jsonify({"error": "User profile instance tracking record missing"}), 404
        
    return jsonify({
        "name": user["name"],
        "email": user["email"]
    }), 200


@auth_bp.route('/profile/update', methods=['PUT'])
@jwt_required
def update_profile(current_user_id):
    """Mutate dynamic credential matrices or modify base layout demographic tags."""
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password')

    if not name or not email:
        return jsonify({"error": "Identity parameters cannot hold unassigned records"}), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:
        if password and password.strip():
            # Apply identical hashing system configuration from register methods
            hashed_password = generate_password_hash(password)
            cursor.execute("""
                UPDATE users 
                SET name = ?, email = ?, password_hash = ? 
                WHERE id = ?
            """, (name, email, hashed_password, current_user_id))
        else:
            # Modify baseline data tracking fields while preserving password integrity
            cursor.execute("""
                UPDATE users 
                SET name = ?, email = ? 
                WHERE id = ?
            """, (name, email, current_user_id))
            
        db.commit()
        return jsonify({"status": "success", "message": "Identity matrix parameters modified"}), 200
        
    except sqlite3.IntegrityError:
        return jsonify({"error": "The designated email profile coordinate is already bound to another profile record"}), 409
    except Exception as e:
        return jsonify({"error": f"Internal storage runtime collision: {str(e)}"}), 500


@auth_bp.route('/profile/delete', methods=['DELETE'])
@jwt_required
def delete_account(current_user_id):
    """CRITICAL ENVIRONMENT PURGE: Cascades data clearing actions across dependent storage tables."""
    db = get_db_connection()
    cursor = db.cursor()

    try:
        # 1. Pull user-associated chat tracking rows directly from 'sessions' table
        user_sessions = cursor.execute(
            "SELECT id FROM sessions WHERE user_id = ?", 
            (current_user_id,)
        ).fetchall()
        
        # Unpack cleanly regardless of whether row_factory returns dictionaries or tuples
        session_ids = [s["id"] if hasattr(s, 'keys') else s[0] for s in user_sessions]

        if session_ids:
            # Build string mapping placeholders: e.g., "?, ?, ?"
            placeholders = ",".join("?" for _ in session_ids)
            
            # Phase A: Erase dialogue history rows matching these session markers
            cursor.execute(f"DELETE FROM messages WHERE session_id IN ({placeholders})", session_ids)
            
            # Phase B: Erase peripheral hardware execution telemetry markers
            cursor.execute(f"DELETE FROM hardware_logs WHERE session_id IN ({placeholders})", session_ids)
            
            # Phase C: Erase the thread references from the 'sessions' table
            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (current_user_id,))

        # 2. Complete the final purge phase by dropping the main profile row
        cursor.execute("DELETE FROM users WHERE id = ?", (current_user_id,))
        
        db.commit()
        
        # 3. Formulate structural cookie dropping configuration payload to drop token layer
        response = make_response(jsonify({"status": "success", "message": "User sequence entirely unmapped"}))
        response.set_cookie('session_token', '', expires=0)
        return response
        
    except Exception as e:
        db.rollback() # Gracefully restore state on collision errors
        return jsonify({"error": f"Critical instance data eradication sequence aborted: {str(e)}"}), 500
