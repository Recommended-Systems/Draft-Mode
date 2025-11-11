from flask import Blueprint, render_template, redirect, url_for, request
from models import User, BlogDraft, DraftVersion
from utils.decorators import login_required, get_current_user
from utils.markdown_renderer import render_markdown_safe

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page"""
    current_user = get_current_user()
    if current_user:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing all drafts"""
    user = get_current_user()
    drafts = BlogDraft.query.filter_by(user_id=user.id).order_by(BlogDraft.updated_at.desc()).all()
    return render_template('dashboard.html', user=user, drafts=drafts)

@main_bp.route('/share/<share_token>')
def public_view(share_token):
    """View a publicly shared version without authentication"""
    from flask import abort
    version = DraftVersion.query.filter_by(share_token=share_token).first_or_404()

    # Check if share token is still valid
    if not version.is_share_token_valid():
        abort(410)  # 410 Gone - resource no longer available

    # Safely render markdown with XSS protection
    html_content = render_markdown_safe(version.content)

    return render_template('public_view.html',
                         version=version,
                         draft=version.blog_draft,
                         author=version.blog_draft.author,
                         html_content=html_content)