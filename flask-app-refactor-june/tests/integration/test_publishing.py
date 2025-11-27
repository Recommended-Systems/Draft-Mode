"""
Integration tests for publishing features
Tests Ghost publishing integration
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from models import PublishingPlatform, db

class TestPublishingPlatformConfiguration:
    """Test publishing platform configuration"""

    def test_list_platforms_empty(self, authenticated_client, init_database):
        """Test listing platforms when none configured"""
        response = authenticated_client.get('/api/publish/platforms')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['platforms'] == []

    def test_list_platforms_with_data(self, authenticated_client, init_database, ghost_platform):
        """Test listing configured platforms"""
        response = authenticated_client.get('/api/publish/platforms')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['platforms']) == 1
        assert data['platforms'][0]['type'] == 'ghost'
        assert data['platforms'][0]['url'] == 'https://test.ghost.io'

    def test_add_ghost_platform(self, authenticated_client, init_database):
        """Test adding Ghost platform configuration"""
        response = authenticated_client.post('/api/publish/platforms/ghost',
            json={
                'platform_url': 'https://mysite.ghost.io',
                'api_key': 'test-key-id:test-key-secret'
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Platform should be in database
        platform = PublishingPlatform.query.filter_by(platform_type='ghost').first()
        assert platform is not None
        assert platform.platform_url == 'https://mysite.ghost.io'

    def test_add_platform_missing_api_key(self, authenticated_client, init_database):
        """Test adding platform without API key"""
        response = authenticated_client.post('/api/publish/platforms/ghost',
            json={
                'platform_url': 'https://mysite.ghost.io',
                'api_key': ''
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_add_ghost_missing_url(self, authenticated_client, init_database):
        """Test adding Ghost without URL"""
        response = authenticated_client.post('/api/publish/platforms/ghost',
            json={
                'platform_url': '',
                'api_key': 'test-key'
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_update_existing_platform(self, authenticated_client, init_database, ghost_platform):
        """Test updating existing platform configuration"""
        response = authenticated_client.post('/api/publish/platforms/ghost',
            json={
                'platform_url': 'https://updated.ghost.io',
                'api_key': 'new-key-id:new-key-secret'
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Should still be only one platform
        platforms = PublishingPlatform.query.filter_by(platform_type='ghost').all()
        assert len(platforms) == 1
        assert platforms[0].platform_url == 'https://updated.ghost.io'

    def test_remove_platform(self, authenticated_client, init_database, ghost_platform):
        """Test removing platform configuration"""
        platform_id = ghost_platform.id

        response = authenticated_client.delete(f'/api/publish/platforms/{platform_id}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Platform should be deleted
        platform = PublishingPlatform.query.get(platform_id)
        assert platform is None

    def test_remove_nonexistent_platform(self, authenticated_client, init_database):
        """Test removing non-existent platform"""
        response = authenticated_client.delete('/api/publish/platforms/9999')

        assert response.status_code == 404

    def test_platform_requires_authentication(self, client, init_database):
        """Test platform endpoints require authentication"""
        # List platforms
        response = client.get('/api/publish/platforms')
        assert response.status_code == 302  # Redirect to login

        # Add platform
        response = client.post('/api/publish/platforms/ghost', json={})
        assert response.status_code == 302


class TestGhostPublishing:
    """Test Ghost publishing functionality"""

    @patch('routes.publish.requests.post')
    def test_publish_to_ghost_success(self, mock_post, authenticated_client, init_database,
                                     test_draft, ghost_platform, mock_ghost_response):
        """Test successful publishing to Ghost"""
        # Mock successful Ghost API response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = mock_ghost_response
        mock_post.return_value = mock_response

        version_id = test_draft.versions[0].id

        response = authenticated_client.post(f'/api/publish/ghost/{version_id}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'edit_url' in data
        assert 'ghost_post_id' in data

    def test_publish_without_platform_configured(self, authenticated_client, init_database, test_draft):
        """Test publishing when no Ghost platform configured"""
        version_id = test_draft.versions[0].id

        response = authenticated_client.post(f'/api/publish/ghost/{version_id}')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not configured' in data['error'].lower()

    @patch('routes.publish.requests.post')
    def test_publish_ghost_api_error(self, mock_post, authenticated_client, init_database,
                                    test_draft, ghost_platform):
        """Test Ghost API returning an error"""
        # Mock Ghost API error
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.json.return_value = {
            'errors': [{'message': 'Validation failed'}]
        }
        mock_post.return_value = mock_response

        version_id = test_draft.versions[0].id

        response = authenticated_client.post(f'/api/publish/ghost/{version_id}')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Ghost API error' in data['error']

    @patch('routes.publish.requests.post')
    def test_publish_connection_error(self, mock_post, authenticated_client, init_database,
                                     test_draft, ghost_platform):
        """Test Ghost publishing with connection error"""
        # Mock connection error
        mock_post.side_effect = Exception('Connection timeout')

        version_id = test_draft.versions[0].id

        response = authenticated_client.post(f'/api/publish/ghost/{version_id}')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False

    def test_publish_nonexistent_version(self, authenticated_client, init_database, ghost_platform):
        """Test publishing non-existent version"""
        response = authenticated_client.post('/api/publish/ghost/9999')

        assert response.status_code == 404

    def test_publish_other_users_draft(self, authenticated_client, init_database,
                                      second_user, ghost_platform):
        """Test cannot publish another user's draft"""
        # Create draft for second user
        from models import BlogDraft, DraftVersion
        draft = BlogDraft(
            title='Other User Draft',
            user_id=second_user.id,
            status='draft'
        )
        db.session.add(draft)
        db.session.commit()

        version = DraftVersion(
            version_name='v1.0',
            content='Content',
            blog_draft_id=draft.id,
            is_current=True
        )
        db.session.add(version)
        db.session.commit()

        # Try to publish with first user's credentials
        response = authenticated_client.post(f'/api/publish/ghost/{version.id}')

        assert response.status_code == 404  # Should not find version

    @patch('routes.publish.requests.post')
    def test_publish_updates_last_used(self, mock_post, authenticated_client, init_database,
                                      test_draft, ghost_platform, mock_ghost_response):
        """Test publishing updates platform last_used_at"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = mock_ghost_response
        mock_post.return_value = mock_response

        # Platform last_used should be None initially
        assert ghost_platform.last_used_at is None

        version_id = test_draft.versions[0].id
        authenticated_client.post(f'/api/publish/ghost/{version_id}')

        # Refresh from database
        db.session.refresh(ghost_platform)

        # last_used_at should now be set
        assert ghost_platform.last_used_at is not None


class TestGhostConnectionTest:
    """Test Ghost connection testing"""

    @patch('routes.publish.requests.get')
    def test_test_ghost_connection_success(self, mock_get, authenticated_client, init_database):
        """Test successful Ghost connection test"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 401  # 401 is expected without auth
        mock_get.return_value = mock_response

        response = authenticated_client.post('/api/publish/test-ghost',
            json={'platform_url': 'https://mysite.ghost.io'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    @patch('routes.publish.requests.get')
    def test_test_ghost_connection_failure(self, mock_get, authenticated_client, init_database):
        """Test failed Ghost connection test"""
        # Mock connection error
        mock_get.side_effect = Exception('Connection failed')

        response = authenticated_client.post('/api/publish/test-ghost',
            json={'platform_url': 'https://invalid.ghost.io'}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_test_ghost_missing_url(self, authenticated_client, init_database):
        """Test Ghost connection test without URL"""
        response = authenticated_client.post('/api/publish/test-ghost',
            json={'platform_url': ''}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
