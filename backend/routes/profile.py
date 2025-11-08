import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from ..models import User, Friendship
from ..extensions import db
from ..helpers import sanitize_content

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile/<int:user_id>', methods=['GET'])
@jwt_required()
def get_profile(user_id):
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    current_user = User.query.get(current_user_id)
    
    is_friend = Friendship.query.filter(
        ((Friendship.user_id == current_user_id) & (Friendship.friend_id == user_id)) |
        ((Friendship.user_id == user_id) & (Friendship.friend_id == current_user_id)),
        Friendship.status == 'accepted'
    ).first() is not None
    
    is_following = current_user.is_following(user)
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email if is_friend or user_id == current_user_id else None,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'bio': user.bio,
        'profile_picture': user.profile_picture,
        'cover_photo': user.cover_photo,
        'is_verified': user.is_verified,
        'is_online': user.is_online,
        'last_seen': user.last_seen.isoformat(),
        'location': user.location,
        'website': user.website,
        'relationship_status': user.relationship_status,
        'work': user.work,
        'education': user.education,
        'created_at': user.created_at.isoformat(),
        'followers_count': user.followers.count(),
        'following_count': user.following.count(),
        'posts_count': user.posts.count(),
        'is_friend': is_friend,
        'is_following': is_following,
        'mutual_friends': len(set(current_user.following.all()) & set(user.following.all()))
    }), 200

@profile_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    data = request.get_json()
    
    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    user.bio = sanitize_content(data.get('bio', user.bio or ''))
    user.location = data.get('location', user.location)
    user.website = data.get('website', user.website)
    user.relationship_status = data.get('relationship_status', user.relationship_status)
    user.work = data.get('work', user.work)
    user.education = data.get('education', user.education)
    
    if 'privacy_settings' in data:
        user.privacy_settings = data['privacy_settings']
    
    db.session.commit()
    
    return jsonify({'message': 'Your profile has been updated successfully!'}), 200

@profile_bp.route('/upload/profile-picture', methods=['POST'])
@jwt_required()
def upload_profile_picture():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if 'file' not in request.files:
        return jsonify({'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400
    
    filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles', filename)
    file.save(filepath)
    
    # We store a web-accessible path, assuming /uploads is served
    user.profile_picture = f'/uploads/profiles/{filename}'
    db.session.commit()
    
    return jsonify({'message': 'Profile picture updated!', 'url': user.profile_picture}), 200