import re
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime
from ..models import User
from ..extensions import db, limiter

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    data = request.get_json()
    
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', data['username']):
        return jsonify({'message': 'Username must be 3-20 characters and contain only letters, numbers, and underscores'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400
    
    if len(data['password']) < 8:
        return jsonify({'message': 'Password must be at least 8 characters'}), 400
    
    hashed_password = generate_password_hash(data['password'])
    
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_password,
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
        birth_date=datetime.strptime(data['birth_date'], '%Y-%m-%d').date() if data.get('birth_date') else None,
        gender=data.get('gender')
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'message': 'Welcome to the community! Your account has been created successfully.',
        'user_id': new_user.id
    }), 201

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    user.is_online = True
    user.last_seen = datetime.utcnow()
    db.session.commit()
    
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'access_token': access_token,
        'message': f'Welcome back, {user.first_name}!',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile_picture': user.profile_picture,
            'is_verified': user.is_verified
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user:
        user.is_online = False
        user.last_seen = datetime.utcnow()
        db.session.commit()
    
    return jsonify({'message': 'See you soon!'}), 200