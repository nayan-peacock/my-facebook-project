from backend.extensions import socketio, db
from backend.models import User
from flask_socketio import emit, join_room, leave_room
from datetime import datetime

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('join')
def handle_join(data):
    room = f'user_{data["user_id"]}'
    join_room(room)
    user = User.query.get(data['user_id'])
    if user:
        user.is_online = True
        db.session.commit()

@socketio.on('leave')
def handle_leave(data):
    room = f'user_{data["user_id"]}'
    leave_room(room)
    user = User.query.get(data['user_id'])
    if user:
        user.is_online = False
        user.last_seen = datetime.utcnow()
        db.session.commit()

@socketio.on('typing')
def handle_typing(data):
    socketio.emit('user_typing', {
        'user_id': data['user_id'],
        'is_typing': data['is_typing']
    }, room=f'user_{data["receiver_id"]}')