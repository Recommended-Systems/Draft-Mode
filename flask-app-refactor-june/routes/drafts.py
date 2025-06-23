from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from models import db, User, BlogDraft, DraftVersion
from utils.decorators import login_required, get_current_user
import markdown
import secrets

drafts_bp = Blueprint('drafts', __name__)

@drafts_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_draft():
    """Create a new blog draft"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        if not title:
            flash('Draft title is required')
            return render_template('create_draft.html')
        
        user = get_current_user()
        
        try:
            # Create draft
            draft = BlogDraft(
                title=title,
                description=description,
                user_id=user.id
            )
            db.session.add(draft)
            db.session.flush()  # Get draft ID
            
            # Create initial version
            version = DraftVersion(
                version_name='v1.0',
                content=f'# {title}\n\nStart writing your blog post here...',
                blog_draft_id=draft.id,
                is_current=True
            )
            db.session.add(version)
            db.session.commit()
            
            flash('Draft created successfully!', 'success')
            return redirect(url_for('drafts.edit_draft', draft_id=draft.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the draft')
            return render_template('create_draft.html')
    
    return render_template('create_draft.html')

@drafts_bp.route('/<int:draft_id>')
@login_required
def edit_draft(draft_id):
    """Edit a specific draft"""
    user = get_current_user()
    draft = BlogDraft.query.filter_by(id=draft_id, user_id=user.id).first_or_404()
    
    # Check if specific version requested
    version_id = request.args.get('version')
    if version_id:
        current_version = DraftVersion.query.filter_by(
            id=version_id, 
            blog_draft_id=draft.id
        ).first()
        if current_version:
            # Update current version flag
            current_version.set_as_current()
    else:
        current_version = draft.current_version
    
    if not current_version:
        flash('No versions found for this draft')
        return redirect(url_for('main.dashboard'))
    
    versions = DraftVersion.query.filter_by(
        blog_draft_id=draft.id
    ).order_by(DraftVersion.created_at.desc()).all()
    
    return render_template('edit_draft.html', 
                         draft=draft, 
                         current_version=current_version, 
                         versions=versions)

@drafts_bp.route('/<int:draft_id>/versions', methods=['POST'])
@login_required
def create_version(draft_id):
    """Create a new version of a draft"""
    user = get_current_user()
    draft = BlogDraft.query.filter_by(id=draft_id, user_id=user.id).first_or_404()
    
    version_name = request.form.get('version_name', '').strip()
    content = request.form.get('content', '')
    
    if not version_name:
        return jsonify({'success': False, 'error': 'Version name is required'})
    
    try:
        # Unset current version
        DraftVersion.query.filter_by(
            blog_draft_id=draft.id, 
            is_current=True
        ).update({'is_current': False})
        
        # Create new version
        version = DraftVersion(
            version_name=version_name,
            content=content,
            blog_draft_id=draft.id,
            is_current=True
        )
        db.session.add(version)
        db.session.commit()
        
        return jsonify({'success': True, 'version_id': version.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to create version'})

@drafts_bp.route('/versions/<int:version_id>/save', methods=['POST'])
@login_required
def save_version(version_id):
    """Save content to a version"""
    user = get_current_user()
    version = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    content = request.json.get('content', '') if request.is_json else request.form.get('content', '')
    
    try:
        version.content = content
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to save content'})

@drafts_bp.route('/versions/<int:version_id>/preview', methods=['POST'])
@login_required
def preview_version(version_id):
    """Preview markdown content as HTML"""
    user = get_current_user()
    version = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    # Get content from request if provided, otherwise use saved content
    content = request.json.get('content', version.content) if request.is_json else version.content
    
    try:
        html_content = markdown.markdown(
            content, 
            extensions=['extra', 'codehilite', 'fenced_code']
        )
    except Exception:
        # Fallback to basic markdown if extensions fail
        html_content = markdown.markdown(content)
    
    return jsonify({'html': html_content})

@drafts_bp.route('/preview', methods=['POST'])
@login_required
def preview_content():
    """Preview content without needing a specific version ID"""
    content = request.json.get('content', '') if request.is_json else ''
    
    try:
        html_content = markdown.markdown(
            content, 
            extensions=['extra', 'codehilite', 'fenced_code']
        )
    except Exception:
        # Fallback to basic markdown if extensions fail
        html_content = markdown.markdown(content)
    
    return jsonify({'html': html_content})

@drafts_bp.route('/compare/<int:version1_id>/<int:version2_id>')
@login_required
def compare_versions(version1_id, version2_id):
    """Compare two versions of a draft"""
    user = get_current_user()
    
    version1 = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version1_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    version2 = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version2_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    # Ensure both versions belong to the same draft
    if version1.blog_draft_id != version2.blog_draft_id:
        flash('Cannot compare versions from different drafts')
        return redirect(url_for('main.dashboard'))
    
    return render_template('compare.html', 
                         draft=version1.blog_draft,
                         version1=version1, 
                         version2=version2)

@drafts_bp.route('/<int:draft_id>/rename', methods=['POST'])
@login_required
def rename_draft(draft_id):
    """Rename a blog draft"""
    user = get_current_user()
    draft = BlogDraft.query.filter_by(id=draft_id, user_id=user.id).first_or_404()
    
    new_name = request.json.get('name', '').strip()
    if not new_name:
        return jsonify({'success': False, 'error': 'Name cannot be empty'})
    
    try:
        draft.title = new_name
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to rename draft'})

@drafts_bp.route('/versions/<int:version_id>/rename', methods=['POST'])
@login_required
def rename_version(version_id):
    """Rename a draft version"""
    user = get_current_user()
    version = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    new_name = request.json.get('name', '').strip()
    if not new_name:
        return jsonify({'success': False, 'error': 'Name cannot be empty'})
    
    try:
        version.version_name = new_name
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to rename version'})

@drafts_bp.route('/versions/<int:version_id>/mark_final', methods=['POST'])
@login_required
def mark_final(version_id):
    """Mark a version as final/published"""
    user = get_current_user()
    version = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    final_name = request.json.get('name', '').strip()
    if not final_name:
        return jsonify({'success': False, 'error': 'Final name cannot be empty'})
    
    try:
        # Update version name to indicate it's final
        version.version_name = final_name
        
        # Generate a share token if it doesn't exist
        version.generate_share_token()
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to mark as final'})

@drafts_bp.route('/versions/<int:version_id>/delete', methods=['POST'])
@login_required
def delete_version(version_id):
    """Delete a draft version (with safety checks)"""
    user = get_current_user()
    version = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    # Check if this is the only version
    version_count = DraftVersion.query.filter_by(blog_draft_id=version.blog_draft_id).count()
    if version_count <= 1:
        return jsonify({'success': False, 'error': 'Cannot delete the only version of a draft'})
    
    try:
        # If this is the current version, set another version as current
        if version.is_current:
            other_version = DraftVersion.query.filter(
                DraftVersion.blog_draft_id == version.blog_draft_id,
                DraftVersion.id != version.id
            ).order_by(DraftVersion.created_at.desc()).first()
            
            if other_version:
                other_version.is_current = True
        
        db.session.delete(version)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to delete version'})

@drafts_bp.route('/<int:draft_id>/delete', methods=['POST'])
@login_required
def delete_draft(draft_id):
    """Delete an entire draft and all its versions"""
    user = get_current_user()
    draft = BlogDraft.query.filter_by(id=draft_id, user_id=user.id).first_or_404()
    
    try:
        # This will cascade delete all versions due to the relationship setup
        db.session.delete(draft)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to delete draft'})

@drafts_bp.route('/versions/<int:version_id>/duplicate', methods=['POST'])
@login_required
def duplicate_version(version_id):
    """Create a duplicate of an existing version"""
    user = get_current_user()
    original_version = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    new_name = request.json.get('name', f"{original_version.version_name} (Copy)")
    
    try:
        # Unset current version flag from other versions
        DraftVersion.query.filter_by(
            blog_draft_id=original_version.blog_draft_id, 
            is_current=True
        ).update({'is_current': False})
        
        # Create duplicate version
        duplicate = DraftVersion(
            version_name=new_name,
            content=original_version.content,
            blog_draft_id=original_version.blog_draft_id,
            is_current=True
        )
        
        db.session.add(duplicate)
        db.session.commit()
        
        return jsonify({'success': True, 'version_id': duplicate.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to duplicate version'})

@drafts_bp.route('/versions/<int:version_id>/share', methods=['POST'])
@login_required
def generate_share_link(version_id):
    """Generate a public share link for a version"""
    user = get_current_user()
    version = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version_id,
        BlogDraft.user_id == user.id
    ).first_or_404()
    
    try:
        # Generate share token if it doesn't exist
        version.generate_share_token()
        db.session.commit()
        
        share_url = url_for('main.public_view', share_token=version.share_token, _external=True)
        return jsonify({'success': True, 'share_url': share_url})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to generate share link'})