from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..models import Story, User
from ..extensions import db

stories_bp = Blueprint('stories', __name__)

@stories_bp.route('/stories', methods=['POST'])
@jwt_required()
def create_story():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    new_story = Story(
        user_id=current_user_id,
        media_type=data.get('media_type', 'text'),
        media_url=data.get('media_url'),
        text=data.get('text', ''),
        background_color=data.get('background_color', '#000000'),
        duration=data.get('duration', 24)
    )
    
    db.session.add(new_story)
    db.session.commit()
    
    return jsonify({'message': 'Story published!', 'story_id': new_story.id}), 201

@stories_bp.route('/stories', methods=['GET'])
@jwt_required()
def get_stories():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    friends = [f.id for f in user.following.all()]
    friends.append(current_user_id)
    
    stories = Story.query.filter(
        Story.user_id.in_(friends),
        Story.expires_at > datetime.utcnow()
    ).order_by(Story.created_at.desc()).all()
    
    stories_by_user = {}
    for story in stories:
        if story.user_id not in stories_by_user:
            stories_by_user[story.user_id] = {
                'user': {
                    'id': story.author.id,
                    'username': story.author.username,
                    'first_name': story.author.first_name,
                    'last_name': story.author.last_name,
                    'profile_picture': story.author.profile_picture
                },
                'stories': []
            }
        
        stories_by_user[story.user_id]['stories'].append({
            'id': story.id,
            'media_type': story.media_type,
            'media_url': story.media_url,
            'text': story.text,
            'background_color': story.background_color,
            'created_at': story.created_at.isoformat(),
            'expires_at': story.expires_at.isoformat(),
            'views_count': len(story.views if story.views else []) # Handle None
        })
    
    return jsonify({'stories': list(stories_by_user.values())}), 200

@stories_bp.route('/stories/<int:story_id>/view', methods=['POST'])
@jwt_required()
def view_story(story_id):
    current_user_id = get_jwt_identity()
    story = Story.query.get_or_404(story_id)
    
    # Handle if story.views is None (though default is [])
    if story.views is None:
        story.views = []

    if current_user_id not in story.views:
        # This is tricky because JSON lists aren't mutable in-place like this.
        # A more robust way:
        current_views = list(story.views)
        current_views.append(current_user_id)
        story.views = current_views
        
        db.session.commit()
    
    return jsonify({'message': 'Story viewed'}), 200