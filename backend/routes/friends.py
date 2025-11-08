from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User, Friendship, Post
from ..extensions import db
from ..helpers import create_notification

friends_bp = Blueprint('friends', __name__)

@friends_bp.route('/friends/request', methods=['POST'])
@jwt_required()
def send_friend_request():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    friend_id = data['friend_id']
    
    if current_user_id == friend_id:
        return jsonify({'message': 'You cannot send a friend request to yourself'}), 400
    
    existing = Friendship.query.filter(
        ((Friendship.user_id == current_user_id) & (Friendship.friend_id == friend_id)) |
        ((Friendship.user_id == friend_id) & (Friendship.friend_id == current_user_id))
    ).first()
    
    if existing:
        return jsonify({'message': 'Friend request already exists or you are already friends'}), 400
    
    friendship = Friendship(user_id=current_user_id, friend_id=friend_id)
    db.session.add(friendship)
    db.session.commit()
    
    create_notification(
        friend_id,
        current_user_id,
        'friend_request',
        'sent you a friend request',
        f'/profile/{current_user_id}'
    )
    
    return jsonify({'message': 'Friend request sent!'}), 201

@friends_bp.route('/friends/accept/<int:friendship_id>', methods=['PUT'])
@jwt_required()
def accept_friend_request(friendship_id):
    current_user_id = get_jwt_identity()
    friendship = Friendship.query.get_or_404(friendship_id)
    
    if friendship.friend_id != current_user_id:
        return jsonify({'message': 'You can only accept friend requests sent to you'}), 403
    
    friendship.status = 'accepted'
    
    current_user = User.query.get(current_user_id)
    friend = User.query.get(friendship.user_id)
    current_user.follow(friend)
    friend.follow(current_user)
    
    db.session.commit()
    
    create_notification(
        friendship.user_id,
        current_user_id,
        'friend_accept',
        'accepted your friend request',
        f'/profile/{current_user_id}'
    )
    
    return jsonify({'message': f'You and {friend.first_name} are now friends!'}), 200

@friends_bp.route('/friends/reject/<int:friendship_id>', methods=['DELETE'])
@jwt_required()
def reject_friend_request(friendship_id):
    current_user_id = get_jwt_identity()
    friendship = Friendship.query.get_or_404(friendship_id)
    
    if friendship.friend_id != current_user_id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    db.session.delete(friendship)
    db.session.commit()
    
    return jsonify({'message': 'Friend request declined'}), 200

@friends_bp.route('/friends/requests', methods=['GET'])
@jwt_required()
def get_friend_requests():
    current_user_id = get_jwt_identity()
    
    requests = Friendship.query.filter_by(friend_id=current_user_id, status='pending').all()
    
    requests_data = [{
        'id': r.id,
        'user': {
            'id': r.user.id,
            'username': r.user.username,
            'first_name': r.user.first_name,
            'last_name': r.user.last_name,
            'profile_picture': r.user.profile_picture
        },
        'created_at': r.created_at.isoformat()
    } for r in requests]
    
    return jsonify({'friend_requests': requests_data}), 200

@friends_bp.route('/friends', methods=['GET'])
@jwt_required()
def get_friends():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    friends = user.following.all()
    
    friends_data = [{
        'id': f.id,
        'username': f.username,
        'first_name': f.first_name,
        'last_name': f.last_name,
        'profile_picture': f.profile_picture,
        'is_online': f.is_online,
        'last_seen': f.last_seen.isoformat()
    } for f in friends]
    
    return jsonify({'friends': friends_data}), 200

@friends_bp.route('/friends/unfriend/<int:friend_id>', methods=['DELETE'])
@jwt_required()
def unfriend(friend_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    friend = User.query.get_or_404(friend_id)
    
    current_user.unfollow(friend)
    friend.unfollow(current_user)
    
    friendship = Friendship.query.filter(
        ((Friendship.user_id == current_user_id) & (Friendship.friend_id == friend_id)) |
        ((Friendship.user_id == friend_id) & (Friendship.friend_id == current_user_id))
    ).first()
    
    if friendship:
        db.session.delete(friendship)
    
    db.session.commit()
    
    return jsonify({'message': 'Friend removed'}), 200

@friends_bp.route('/follow/<int:user_id>', methods=['POST'])
@jwt_required()
def follow_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    user_to_follow = User.query.get_or_404(user_id)
    
    if current_user_id == user_id:
        return jsonify({'message': 'You cannot follow yourself'}), 400
    
    current_user.follow(user_to_follow)
    db.session.commit()
    
    create_notification(
        user_id,
        current_user_id,
        'follow',
        'started following you',
        f'/profile/{current_user_id}'
    )
    
    return jsonify({'message': f'You are now following {user_to_follow.first_name}!'}), 200

@friends_bp.route('/unfollow/<int:user_id>', methods=['DELETE'])
@jwt_required()
def unfollow_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    user_to_unfollow = User.query.get_or_404(user_id)
    
    current_user.unfollow(user_to_unfollow)
    db.session.commit()
    
    return jsonify({'message': f'You unfollowed {user_to_unfollow.first_name}'}), 200

@friends_bp.route('/search', methods=['GET'])
@jwt_required()
def search():
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')
    
    results = {}
    
    if search_type in ['all', 'users']:
        users = User.query.filter(
            (User.username.ilike(f'%{query}%')) |
            (User.first_name.ilike(f'%{query}%')) |
            (User.last_name.ilike(f'%{query}%'))
        ).limit(20).all()
        
        results['users'] = [{
            'id': u.id,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'profile_picture': u.profile_picture,
            'is_verified': u.is_verified
        } for u in users]
    
    if search_type in ['all', 'posts']:
        posts = Post.query.filter(Post.content.ilike(f'%{query}%')).order_by(Post.created_at.desc()).limit(20).all()
        
        results['posts'] = [{
            'id': p.id,
            'content': p.content[:200] + '...' if len(p.content) > 200 else p.content,
            'author': {
                'id': p.author.id,
                'username': p.author.username,
                'first_name': p.author.first_name,
                'profile_picture': p.author.profile_picture
            },
            'created_at': p.created_at.isoformat()
        } for p in posts]
    
    return jsonify(results), 200