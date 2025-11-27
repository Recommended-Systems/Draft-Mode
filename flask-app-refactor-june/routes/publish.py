"""
Publishing routes for pushing drafts to external platforms
Currently supports: Ghost
Future: Substack, Buttondown, Beehiiv
"""
from flask import Blueprint, request, jsonify, current_app
from models import db, PublishingPlatform, DraftVersion, BlogDraft
from utils.decorators import login_required, get_current_user
from utils.encryption import encrypt_api_key, decrypt_api_key
import requests
import jwt
from datetime import datetime as dt, timedelta
import json

publish_bp = Blueprint('publish', __name__)

# ============================================================================
# Platform Configuration Routes
# ============================================================================

@publish_bp.route('/platforms', methods=['GET'])
@login_required
def list_platforms():
    """Get all configured publishing platforms for current user"""
    user = get_current_user()

    platforms = PublishingPlatform.query.filter_by(
        user_id=user.id,
        is_active=True
    ).all()

    return jsonify({
        'platforms': [{
            'id': p.id,
            'type': p.platform_type,
            'url': p.platform_url,
            'created_at': p.created_at.isoformat() if p.created_at else None,
            'last_used': p.last_used_at.isoformat() if p.last_used_at else None
        } for p in platforms]
    })

@publish_bp.route('/platforms/<platform_type>', methods=['POST'])
@login_required
def add_platform(platform_type):
    """
    Add or update a publishing platform configuration

    Supported platforms: ghost, substack, buttondown, beehiiv
    """
    user = get_current_user()

    valid_platforms = ['ghost', 'substack', 'buttondown', 'beehiiv']
    if platform_type not in valid_platforms:
        return jsonify({
            'success': False,
            'error': f'Invalid platform. Supported: {", ".join(valid_platforms)}'
        }), 400

    data = request.get_json()
    api_key = data.get('api_key', '').strip()
    platform_url = data.get('platform_url', '').strip()

    if not api_key:
        return jsonify({'success': False, 'error': 'API key is required'}), 400

    if platform_type == 'ghost' and not platform_url:
        return jsonify({'success': False, 'error': 'Ghost URL is required'}), 400

    try:
        # Check if platform already exists
        existing = PublishingPlatform.query.filter_by(
            user_id=user.id,
            platform_type=platform_type
        ).first()

        if existing:
            # Update existing
            existing.encrypted_api_key = encrypt_api_key(api_key)
            existing.platform_url = platform_url
            existing.updated_at = dt.utcnow()
            existing.is_active = True
        else:
            # Create new
            platform = PublishingPlatform(
                user_id=user.id,
                platform_type=platform_type,
                platform_url=platform_url,
                encrypted_api_key=encrypt_api_key(api_key),
                is_active=True
            )
            db.session.add(platform)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'{platform_type.capitalize()} configured successfully'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving platform config: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to save configuration'
        }), 500

@publish_bp.route('/platforms/<int:platform_id>', methods=['DELETE'])
@login_required
def remove_platform(platform_id):
    """Remove a publishing platform configuration"""
    user = get_current_user()

    platform = PublishingPlatform.query.filter_by(
        id=platform_id,
        user_id=user.id
    ).first_or_404()

    try:
        db.session.delete(platform)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Platform removed successfully'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing platform: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to remove platform'
        }), 500

@publish_bp.route('/test-ghost', methods=['POST'])
@login_required
def test_ghost_connection():
    """Test Ghost connection server-side to avoid CORS issues"""
    user = get_current_user()
    data = request.get_json()
    ghost_url = data.get('platform_url', '').strip()

    if not ghost_url:
        return jsonify({
            'success': False,
            'error': 'Ghost URL is required'
        }), 400

    try:
        # Test the Ghost API endpoint
        test_url = ghost_url.rstrip('/') + '/ghost/api/admin/site/'

        response = requests.get(
            test_url,
            headers={'Accept': 'application/json'},
            timeout=10
        )

        # 401 is expected without auth - means API is reachable
        if response.status_code in [200, 401]:
            return jsonify({
                'success': True,
                'message': 'Ghost site is reachable! Save your API key to enable publishing.'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Connection failed ({response.status_code}). Please check the URL.'
            }), 400

    except requests.RequestException as e:
        current_app.logger.error(f"Ghost connection test failed: {e}")
        return jsonify({
            'success': False,
            'error': 'Cannot reach Ghost site. Check the URL and ensure it\'s accessible.'
        }), 400

# ============================================================================
# Ghost Publishing
# ============================================================================

def create_ghost_jwt(api_key):
    """
    Create JWT token for Ghost Admin API authentication

    Ghost uses JWT tokens split as 'id:secret'
    """
    try:
        # Split the key into ID and secret
        key_id, key_secret = api_key.split(':')

        # Prepare the token
        iat = int(dt.now().timestamp())

        header = {'alg': 'HS256', 'typ': 'JWT', 'kid': key_id}
        payload = {
            'iat': iat,
            'exp': iat + 5 * 60,  # Token expires in 5 minutes
            'aud': '/admin/'
        }

        # Create token
        token = jwt.encode(payload, bytes.fromhex(key_secret), algorithm='HS256', headers=header)

        return token

    except ValueError:
        raise ValueError("Invalid Ghost API key format. Expected 'id:secret'")
    except Exception as e:
        current_app.logger.error(f"Error creating Ghost JWT: {e}")
        raise ValueError("Failed to create authentication token")

@publish_bp.route('/ghost/<int:version_id>', methods=['POST'])
@login_required
def publish_to_ghost(version_id):
    """
    Publish a draft version to Ghost

    Creates a new post as draft in Ghost
    """
    user = get_current_user()

    # Get the version
    version = DraftVersion.query.join(BlogDraft).filter(
        DraftVersion.id == version_id,
        BlogDraft.user_id == user.id
    ).first_or_404()

    # Get Ghost platform config
    ghost_platform = PublishingPlatform.query.filter_by(
        user_id=user.id,
        platform_type='ghost',
        is_active=True
    ).first()

    if not ghost_platform:
        return jsonify({
            'success': False,
            'error': 'Ghost platform not configured',
            'redirect': '/settings/profile#publishing'
        }), 400

    try:
        # Decrypt API key
        api_key = decrypt_api_key(ghost_platform.encrypted_api_key)

        # Create JWT token
        token = create_ghost_jwt(api_key)

        # Prepare Ghost API request
        ghost_url = ghost_platform.platform_url.rstrip('/')
        api_url = f"{ghost_url}/ghost/api/admin/posts/"

        # Send raw markdown in mobiledoc format
        # Ghost will display it as an editable markdown block
        mobiledoc = {
            'version': '0.3.1',
            'atoms': [],
            'cards': [
                ['markdown', {'markdown': version.content}]
            ],
            'markups': [],
            'sections': [[10, 0]]
        }

        # Prepare post data
        post_data = {
            'posts': [{
                'title': version.blog_draft.title,
                'mobiledoc': json.dumps(mobiledoc),
                'status': 'draft',
                'tags': [],
                'meta_description': version.blog_draft.description or '',
            }]
        }

        # Make request to Ghost API
        headers = {
            'Authorization': f'Ghost {token}',
            'Content-Type': 'application/json',
            'Accept-Version': 'v5.0'  # Ghost API version
        }

        response = requests.post(
            api_url,
            json=post_data,
            headers=headers,
            timeout=30
        )

        if response.status_code in [200, 201]:
            result = response.json()
            ghost_post = result['posts'][0]

            # Update last used timestamp
            ghost_platform.last_used_at = dt.utcnow()
            db.session.commit()

            # Return success with edit link
            admin_url = f"{ghost_url}/ghost/#/editor/post/{ghost_post['id']}"

            return jsonify({
                'success': True,
                'message': 'Published to Ghost successfully',
                'ghost_post_id': ghost_post['id'],
                'edit_url': admin_url,
                'post_url': ghost_post.get('url', '')
            })
        else:
            error_msg = response.json().get('errors', [{}])[0].get('message', 'Unknown error')
            current_app.logger.error(f"Ghost API error: {response.status_code} - {error_msg}")

            return jsonify({
                'success': False,
                'error': f'Ghost API error: {error_msg}'
            }), 500

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except requests.RequestException as e:
        current_app.logger.error(f"Ghost API request failed: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to connect to Ghost. Check your Ghost URL.'
        }), 500
    except Exception as e:
        current_app.logger.error(f"Error publishing to Ghost: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500
