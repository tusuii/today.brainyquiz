from flask import Blueprint, jsonify
from sqlalchemy import text
from app import db

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """
    Health check endpoint for Kubernetes probes.
    Checks database connection and returns status.
    """
    status = {"status": "healthy", "services": {}}
    
    # Check database connection
    try:
        db.session.execute(text('SELECT 1'))
        status["services"]["database"] = "connected"
    except Exception as e:
        status["services"]["database"] = f"error: {str(e)}"
        status["status"] = "unhealthy"
    
    return jsonify(status)
