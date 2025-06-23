from flask import Blueprint, jsonify
from models import User, BlogDraft, DraftVersion
from utils.decorators import login_required, get_current_user

api_bp = Blueprint('api', __name__)

@api_bp.route('/drafts/<int:draft_id>/stats')
@login_required
def get_draft_stats(draft_id):
    """Get statistics for a specific draft"""
    user = get_current_user()
    draft = BlogDraft.query.filter_by(id=draft_id, user_id=user.id).first_or_404()
    
    versions = DraftVersion.query.filter_by(blog_draft_id=draft.id).all()
    
    total_words = 0
    total_chars = 0
    
    for version in versions:
        total_words += version.word_count
        total_chars += version.character_count
    
    current_version = draft.current_version
    current_words = current_version.word_count if current_version else 0
    current_chars = current_version.character_count if current_version else 0
    
    stats = {
        'draft_id': draft.id,
        'title': draft.title,
        'total_versions': len(versions),
        'total_words_all_versions': total_words,
        'total_chars_all_versions': total_chars,
        'current_version_words': current_words,
        'current_version_chars': current_chars,
        'created_at': draft.created_at.isoformat(),
        'updated_at': draft.updated_at.isoformat(),
        'has_final_version': draft.has_final_version
    }
    
    return jsonify(stats)

@api_bp.route('/user/stats')
@login_required
def get_user_stats():
    """Get statistics for the current user"""
    user = get_current_user()
    
    stats = {
        'user_id': user.id,
        'name': user.name,
        'email': user.email,
        'total_drafts': user.total_drafts,
        'total_versions': user.total_versions,
        'member_since': user.created_at.isoformat(),
        'last_updated': user.updated_at.isoformat()
    }
    
    return jsonify(stats)

@api_bp.route('/drafts')
@login_required
def list_drafts():
    """Get list of all drafts for the current user"""
    user = get_current_user()
    drafts = BlogDraft.query.filter_by(user_id=user.id).order_by(BlogDraft.updated_at.desc()).all()
    
    draft_list = []
    for draft in drafts:
        draft_data = {
            'id': draft.id,
            'title': draft.title,
            'description': draft.description,
            'status': draft.status,
            'version_count': len(draft.versions),
            'created_at': draft.created_at.isoformat(),
            'updated_at': draft.updated_at.isoformat(),
            'has_final_version': draft.has_final_version
        }
        
        if draft.current_version:
            draft_data['current_version'] = {
                'id': draft.current_version.id,
                'name': draft.current_version.version_name,
                'word_count': draft.current_version.word_count,
                'character_count': draft.current_version.character_count,
                'updated_at': draft.current_version.updated_at.isoformat()
            }
        
        draft_list.append(draft_data)
    
    return jsonify({
        'drafts': draft_list,
        'total_count': len(draft_list)
    })

@api_bp.route('/drafts/<int:draft_id>/versions')
@login_required
def list_versions(draft_id):
    """Get list of all versions for a specific draft"""
    user = get_current_user()
    draft = BlogDraft.query.filter_by(id=draft_id, user_id=user.id).first_or_404()
    
    versions = DraftVersion.query.filter_by(
        blog_draft_id=draft.id
    ).order_by(DraftVersion.created_at.desc()).all()
    
    version_list = []
    for version in versions:
        version_data = {
            'id': version.id,
            'name': version.version_name,
            'word_count': version.word_count,
            'character_count': version.character_count,
            'is_current': version.is_current,
            'is_final': version.is_final,
            'has_share_token': bool(version.share_token),
            'created_at': version.created_at.isoformat(),
            'updated_at': version.updated_at.isoformat()
        }
        version_list.append(version_data)
    
    return jsonify({
        'draft_id': draft.id,
        'draft_title': draft.title,
        'versions': version_list,
        'total_count': len(version_list)
    })