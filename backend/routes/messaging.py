from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Message, User
from ..extensions import db, socketio
from ..helpers import sanitize_content, create_notification

messaging_bp = Blueprint('messaging', __name__)

@messaging_bp.route('/messages', methods=['POST'])
@jwt_required()
def send_message():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    content = sanitize_content(data['content'])
    
    message = Message(
        sender_id=current_user_id,
        receiver_id=data['receiver_id'],
        content=content,
        image=data.get('image')
    )
    
    db.session.add(message)
    db.session.commit()
    
    sender = User.query.get(current_user_id)
    
    socketio.emit('new_message', {
        'id': message.id,
        'sender': {
            'id': sender.id,
            'username': sender.username,
            'first_name': sender.first_name,
            'profile_picture': sender.profile_picture
        },
        'content': content,
        'created_at': message.created_at.isoformat()
    }, room=f'user_{data["receiver_id"]}')
    
    create_notification(
        data['receiver_id'],
        current_user_id,
        'message',
        f'sent you a message',
        f'/messages/{current_user_id}'
    )
    
    return jsonify({'message': 'Message sent!', 'message_id': message.id}), 201

@messaging_bp.route('/messages/<int:user_id>', methods=['GET'])
@jwt_required()
def get_messages(user_id):
    current_user_id = get_jwt_identity()
    
    messages = Message.query.filter(
        ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
    ).order_by(Message.created_at.asc()).all()
    
    Message.query.filter_by(sender_id=user_id, receiver_id=current_user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    messages_data = [{
        'id': m.id,
        'sender_id': m.sender_id,
        'receiver_id': m.receiver_id,
        'content': m.content,
        'image': m.image,
        'is_read': m.is_read,
        'created_at': m.created_at.isoformat()
    } for m in messages]
    
    return jsonify({'messages': messages_data}), 200

@messaging_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    current_user_id = get_jwt_identity()
    
    sent = db.session.query(Message.receiver_id, db.func.max(Message.created_at)).filter_by(sender_id=current_user_id).group_by(Message.receiver_id).all()
    received = db.session.query(Message.sender_id, db.func.max(Message.created_at)).filter_by(receiver_id=current_user_id).group_by(Message.sender_id).all()
    
    conversations = {}
    for user_id, last_msg_time in sent + received:
        if user_id not in conversations or conversations[user_id] < last_msg_time:
            conversations[user_id] = last_msg_time
    
    conv_data = []
    for user_id, last_time in sorted(conversations.items(), key=lambda x: x[1], reverse=True):
        user = User.query.get(user_id)
        last_msg = Message.query.filter(
            ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
            ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
        ).order_by(Message.created_at.desc()).first()
        
        unread = Message.query.filter_by(sender_id=user_id, receiver_id=current_user_id, is_read=False).count()
        
        conv_data.append({
            'user': {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'profile_picture': user.profile_picture,
                'is_online': user.is_online
            },
            'last_message': {
                'content': last_msg.content[:50] + '...' if len(last_msg.content) > 50 else last_msg.content,
                'created_at': last_msg.created_at.isoformat(),
                'is_own': last_msg.sender_id == current_user_id
            },
            'unread_count': unread
        })
    
    return jsonify({'conversations': conv_data}), 200