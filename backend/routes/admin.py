from flask import Blueprint, request, jsonify
from backend.models import db, User, UserChallenge

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin', methods=['GET'])
def admin_dashboard():
    return jsonify({'error': 'Implementation needed'}), 501