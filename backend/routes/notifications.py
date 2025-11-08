from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Notification
from ..extensions import db

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    current_user_id = get_jwt_identity()
    
    notifications = Notification.query.filter_by(user_id=current_user_id).order_by(Notification.created_at.desc()).limit(50).all()
    
    notif_data = [{
        'id': n.id,
        'type': n.type,
        'content': n.content,
        'link': n.link,
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat(),
        'sender': {
            'id': n.sender.id,
            'username': n.sender.username,
            'first_name': n.sender.first_name,
            'profile_picture': n.sender.profile_picture
        } if n.sender else None
    } for n in notifications]
    
    return jsonify({'notifications': notif_data}), 200

@notifications_bp.route('/notifications/<int:notif_id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_read(notif_id):
    current_user_id = get_jwt_identity()
    notification = Notification.query.get_or_404(notif_id)
    
    if notification.user_id != current_user_id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'message': 'Notification marked as read'}), 200