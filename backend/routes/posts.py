from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from ..models import Post, Like, Comment, CommentLike, Share, SavedPost, User
from ..extensions import db
from ..helpers import sanitize_content, create_notification, get_user_feed

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    content = sanitize_content(data['content'])
    
    new_post = Post(
        content=content,
        images=data.get('images', []),
        video=data.get('video'),
        location=data.get('location'),
        feeling=data.get('feeling'),
        tagged_users=data.get('tagged_users', []),
        privacy=data.get('privacy', 'public'),
        user_id=current_user_id
    )
    
    db.session.add(new_post)
    db.session.commit()
    
    if data.get('tagged_users'):
        for tagged_user_id in data['tagged_users']:
            create_notification(
                tagged_user_id,
                current_user_id,
                'tag',
                f'tagged you in a post',
                f'/post/{new_post.id}'
            )
    
    return jsonify({
        'message': 'Your post has been shared!',
        'post_id': new_post.id,
        'sentiment': 'positive' if new_post.sentiment > 0 else 'negative' if new_post.sentiment < 0 else 'neutral'
    }), 201

@posts_bp.route('/feed', methods=['GET'])
@jwt_required()
def get_feed():
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    posts = get_user_feed(current_user_id, page, per_page)
    
    posts_data = []
    for post in posts.items:
        current_user_liked = Like.query.filter_by(user_id=current_user_id, post_id=post.id).first()
        
        posts_data.append({
            'id': post.id,
            'content': post.content,
            'images': post.images,
            'video': post.video,
            'location': post.location,
            'feeling': post.feeling,
            'privacy': post.privacy,
            'is_edited': post.is_edited,
            'created_at': post.created_at.isoformat(),
            'author': {
                'id': post.author.id,
                'username': post.author.username,
                'first_name': post.author.first_name,
                'last_name': post.author.last_name,
                'profile_picture': post.author.profile_picture,
                'is_verified': post.author.is_verified
            },
            'likes_count': post.likes.count(),
            'comments_count': post.comments.count(),
            'shares_count': post.shares.count(),
            'user_liked': current_user_liked is not None,
            'user_reaction': current_user_liked.reaction_type if current_user_liked else None,
            'reactions': {
                'like': post.likes.filter_by(reaction_type='like').count(),
                'love': post.likes.filter_by(reaction_type='love').count(),
                'haha': post.likes.filter_by(reaction_type='haha').count(),
                'wow': post.likes.filter_by(reaction_type='wow').count(),
                'sad': post.likes.filter_by(reaction_type='sad').count(),
                'angry': post.likes.filter_by(reaction_type='angry').count()
            }
        })
    
    return jsonify({
        'posts': posts_data,
        'total': posts.total,
        'pages': posts.pages,
        'current_page': posts.page,
        'has_next': posts.has_next,
        'has_prev': posts.has_prev
    }), 200

@posts_bp.route('/posts/<int:post_id>', methods=['GET'])
@jwt_required()
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    comments_data = []
    for c in post.comments.filter_by(parent_id=None).order_by(Comment.created_at.desc()).all():
        comments_data.append({
            'id': c.id,
            'content': c.content,
            'image': c.image,
            'is_edited': c.is_edited,
            'created_at': c.created_at.isoformat(),
            'author': {
                'id': c.author.id,
                'username': c.author.username,
                'first_name': c.author.first_name,
                'last_name': c.author.last_name,
                'profile_picture': c.author.profile_picture
            },
            'likes_count': c.likes.count(),
            'replies_count': c.replies.count()
        })
    
    return jsonify({
        'id': post.id,
        'content': post.content,
        'images': post.images,
        'video': post.video,
        'location': post.location,
        'feeling': post.feeling,
        'created_at': post.created_at.isoformat(),
        'author': {
            'id': post.author.id,
            'username': post.author.username,
            'first_name': post.author.first_name,
            'last_name': post.author.last_name,
            'profile_picture': post.author.profile_picture,
            'is_verified': post.author.is_verified
        },
        'likes_count': post.likes.count(),
        'comments': comments_data,
        'shares_count': post.shares.count()
    }), 200

@posts_bp.route('/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    current_user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != current_user_id:
        return jsonify({'message': 'You can only edit your own posts'}), 403
    
    data = request.get_json()
    post.content = sanitize_content(data['content'])
    post.is_edited = True
    post.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'message': 'Post updated successfully!'}), 200

@posts_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    current_user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != current_user_id:
        return jsonify({'message': 'You can only delete your own posts'}), 403
    
    db.session.delete(post)
    db.session.commit()
    
    return jsonify({'message': 'Post deleted successfully'}), 200

@posts_bp.route('/posts/<int:post_id>/react', methods=['POST'])
@jwt_required()
def react_to_post(post_id):
    current_user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    
    reaction_type = data.get('reaction_type', 'like')
    
    existing_like = Like.query.filter_by(user_id=current_user_id, post_id=post_id).first()
    
    if existing_like:
        if existing_like.reaction_type == reaction_type:
            db.session.delete(existing_like)
            db.session.commit()
            return jsonify({'message': 'Reaction removed'}), 200
        else:
            existing_like.reaction_type = reaction_type
            db.session.commit()
            return jsonify({'message': f'Changed reaction to {reaction_type}'}), 200
    
    new_like = Like(user_id=current_user_id, post_id=post_id, reaction_type=reaction_type)
    db.session.add(new_like)
    db.session.commit()
    
    if post.user_id != current_user_id:
        create_notification(
            post.user_id,
            current_user_id,
            'like',
            f'reacted {reaction_type} to your post',
            f'/post/{post_id}'
        )
    
    return jsonify({'message': f'Reacted with {reaction_type}!'}), 201

@posts_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def create_comment(post_id):
    current_user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    
    content = sanitize_content(data['content'])
    
    new_comment = Comment(
        content=content,
        image=data.get('image'),
        user_id=current_user_id,
        post_id=post_id,
        parent_id=data.get('parent_id')
    )
    
    db.session.add(new_comment)
    db.session.commit()
    
    if post.user_id != current_user_id:
        create_notification(
            post.user_id,
            current_user_id,
            'comment',
            f'commented on your post: "{content[:50]}..."',
            f'/post/{post_id}'
        )
    
    return jsonify({
        'message': 'Comment posted!',
        'comment_id': new_comment.id
    }), 201

@posts_bp.route('/comments/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(comment_id):
    current_user_id = get_jwt_identity()
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.user_id != current_user_id:
        return jsonify({'message': 'You can only edit your own comments'}), 403
    
    data = request.get_json()
    comment.content = sanitize_content(data['content'])
    comment.is_edited = True
    
    db.session.commit()
    
    return jsonify({'message': 'Comment updated!'}), 200

@posts_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    current_user_id = get_jwt_identity()
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.user_id != current_user_id:
        return jsonify({'message': 'You can only delete your own comments'}), 403
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'message': 'Comment deleted'}), 200

@posts_bp.route('/comments/<int:comment_id>/like', methods=['POST'])
@jwt_required()
def like_comment(comment_id):
    current_user_id = get_jwt_identity()
    comment = Comment.query.get_or_404(comment_id)
    
    existing = CommentLike.query.filter_by(user_id=current_user_id, comment_id=comment_id).first()
    
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'message': 'Like removed'}), 200
    
    new_like = CommentLike(user_id=current_user_id, comment_id=comment_id)
    db.session.add(new_like)
    db.session.commit()
    
    return jsonify({'message': 'Comment liked!'}), 201

@posts_bp.route('/posts/<int:post_id>/share', methods=['POST'])
@jwt_required()
def share_post(post_id):
    current_user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    
    new_share = Share(
        user_id=current_user_id,
        post_id=post_id,
        caption=data.get('caption', '')
    )
    
    db.session.add(new_share)
    db.session.commit()
    
    if post.user_id != current_user_id:
        create_notification(
            post.user_id,
            current_user_id,
            'share',
            'shared your post',
            f'/post/{post_id}'
        )
    
    return jsonify({'message': 'Post shared to your timeline!'}), 201

@posts_bp.route('/posts/<int:post_id>/save', methods=['POST'])
@jwt_required()
def save_post(post_id):
    current_user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    
    existing = SavedPost.query.filter_by(user_id=current_user_id, post_id=post_id).first()
    
    if existing:
        return jsonify({'message': 'Post already saved'}), 400
    
    saved = SavedPost(
        user_id=current_user_id,
        post_id=post_id,
        collection_name=data.get('collection_name', 'Saved Items')
    )
    
    db.session.add(saved)
    db.session.commit()
    
    return jsonify({'message': 'Post saved successfully!'}), 201

@posts_bp.route('/saved-posts', methods=['GET'])
@jwt_required()
def get_saved_posts():
    current_user_id = get_jwt_identity()
    
    saved = SavedPost.query.filter_by(user_id=current_user_id).order_by(SavedPost.created_at.desc()).all()
    
    posts_data = []
    for s in saved:
        post = s.post
        posts_data.append({
            'id': post.id,
            'content': post.content,
            'images': post.images,
            'created_at': post.created_at.isoformat(),
            'saved_at': s.created_at.isoformat(),
            'collection': s.collection_name,
            'author': {
                'id': post.author.id,
                'username': post.author.username,
                'first_name': post.author.first_name,
                'last_name': post.author.last_name
            }
        })
    
    return jsonify({'saved_posts': posts_data}), 200

@posts_bp.route('/trending', methods=['GET'])
@jwt_required()
def get_trending():
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    trending_posts = db.session.query(Post).join(Like).filter(Post.created_at >= week_ago).group_by(Post.id).order_by(db.func.count(Like.id).desc()).limit(10).all()
    
    posts_data = [{
        'id': p.id,
        'content': p.content,
        'images': p.images,
        'author': {
            'id': p.author.id,
            'username': p.author.username,
            'first_name': p.author.first_name,
            'profile_picture': p.author.profile_picture
        },
        'likes_count': p.likes.count(),
        'comments_count': p.comments.count(),
        'created_at': p.created_at.isoformat()
    } for p in trending_posts]
    
    return jsonify({'trending_posts': posts_data}), 200