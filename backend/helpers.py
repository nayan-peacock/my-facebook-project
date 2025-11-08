import bleach
from .extensions import db, socketio
from .models import Notification, User, Post, Like

def sanitize_content(content):
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li']
    allowed_attributes = {'a': ['href', 'title']}
    return bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes, strip=True)

def create_notification(user_id, sender_id, ntype, content, link=None):
    notification = Notification(
        user_id=user_id,
        sender_id=sender_id,
        type=ntype,
        content=content,
        link=link
    )
    db.session.add(notification)
    db.session.commit()
    
    sender = User.query.get(sender_id)
    socketio.emit('new_notification', {
        'id': notification.id,
        'type': ntype,
        'content': content,
        'sender': sender.username if sender else None,
        'created_at': notification.created_at.isoformat()
    }, room=f'user_{user_id}')

def get_user_feed(user_id, page=1, per_page=10):
    user = User.query.get(user_id)
    friends = [f.id for f in user.following.all()]
    friends.append(user_id)
    
    posts = Post.query.filter(Post.user_id.in_(friends)).order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return posts