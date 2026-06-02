# ==============================================================================
# SYSTEM INSTANCE CODE BASE : JARVIS CORE FRAMEWORK
# MODULE          : blueprints.settings.routes
# DESCRIPTION     : Controls the retrieval and modification of core application settings 
#                   and configuration states mapped to individual user instances.
# COORDINATES     : Layer-3 Backend Logic Blueprint
# SUBSYSTEM       : Application Configurations & User Environment Layer
# ==============================================================================

from flask import Blueprint, request, jsonify
from database import get_db_connection
from blueprints.auth.routes import jwt_required

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET'])
@jwt_required
def get_settings(current_user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT setting_key, setting_value FROM user_settings WHERE user_id = ?", (current_user_id,))
        settings = {row['setting_key']: row['setting_value'] for row in cursor.fetchall()}
    return jsonify({"status": "success", "settings": settings})

@settings_bp.route('/settings/update', methods=['POST'])
@jwt_required
def update_setting(current_user_id):
    data = request.get_json() or {}
    key = data.get('key')
    value = data.get('value')
    
    if not key or value is None:
        return jsonify({"error": "Key and Value required"}), 400
        
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_settings (user_id, setting_key, setting_value) 
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, setting_key) DO UPDATE SET setting_value = excluded.setting_value
        """, (current_user_id, key, str(value)))
        conn.commit()
        
    return jsonify({"status": "success", "message": f"Setting {key} updated"})
