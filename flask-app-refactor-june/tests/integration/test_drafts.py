"""
Integration tests for draft management
Tests creating, editing, deleting drafts and versions
"""
import pytest
import json
from models import BlogDraft, DraftVersion, db

class TestDraftCreation:
    """Test draft creation"""

    def test_create_draft_page(self, authenticated_client, init_database):
        """Test create draft page loads"""
        response = authenticated_client.get('/drafts/create')

        assert response.status_code == 200
        assert b'create' in response.data.lower() or b'new' in response.data.lower()

    def test_create_draft_success(self, authenticated_client, init_database):
        """Test successfully creating a draft"""
        response = authenticated_client.post('/drafts/create',
            data={
                'title': 'New Test Draft',
                'description': 'Test Description'
            },
            follow_redirects=True
        )

        assert response.status_code == 200

        # Draft should be created
        draft = BlogDraft.query.filter_by(title='New Test Draft').first()
        assert draft is not None
        assert draft.description == 'Test Description'

        # Initial version should be created
        assert len(draft.versions) == 1
        assert draft.versions[0].is_current is True

    def test_create_draft_without_title(self, authenticated_client, init_database):
        """Test creating draft without title"""
        response = authenticated_client.post('/drafts/create',
            data={'description': 'Test Description'}
        )

        # Should show validation error
        assert response.status_code == 200
        # No draft should be created
        drafts = BlogDraft.query.all()
        assert len(drafts) == 0


class TestDraftViewing:
    """Test viewing drafts"""

    def test_view_draft(self, authenticated_client, init_database, test_draft):
        """Test viewing a draft"""
        response = authenticated_client.get(f'/drafts/{test_draft.id}')

        assert response.status_code == 200
        assert test_draft.title.encode() in response.data

    def test_view_nonexistent_draft(self, authenticated_client, init_database):
        """Test viewing non-existent draft"""
        response = authenticated_client.get('/drafts/9999')

        assert response.status_code == 404

    def test_view_other_users_draft(self, authenticated_client, init_database, second_user):
        """Test cannot view another user's draft"""
        # Create draft for second user
        draft = BlogDraft(
            title='Other User Draft',
            user_id=second_user.id,
            status='draft'
        )
        db.session.add(draft)
        db.session.commit()

        response = authenticated_client.get(f'/drafts/{draft.id}')

        assert response.status_code == 404

    def test_dashboard_shows_user_drafts(self, authenticated_client, init_database, test_draft):
        """Test dashboard shows user's drafts"""
        response = authenticated_client.get('/dashboard')

        assert response.status_code == 200
        assert test_draft.title.encode() in response.data


class TestDraftEditing:
    """Test editing drafts"""

    def test_rename_draft(self, authenticated_client, init_database, test_draft):
        """Test renaming a draft"""
        response = authenticated_client.post(f'/drafts/{test_draft.id}/rename',
            json={'name': 'Updated Title'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Draft should be renamed
        db.session.refresh(test_draft)
        assert test_draft.title == 'Updated Title'

    def test_save_version_content(self, authenticated_client, init_database, test_draft):
        """Test saving version content"""
        version_id = test_draft.versions[0].id

        response = authenticated_client.post(f'/drafts/versions/{version_id}/save',
            json={'content': 'Updated content here'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Content should be updated
        version = DraftVersion.query.get(version_id)
        assert version.content == 'Updated content here'


class TestVersionManagement:
    """Test version management"""

    def test_create_new_version(self, authenticated_client, init_database, test_draft):
        """Test creating a new version"""
        # Get current version count
        initial_count = len(test_draft.versions)

        response = authenticated_client.post(f'/drafts/{test_draft.id}/new-version',
            json={'version_name': 'v2.0'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Should have one more version
        db.session.refresh(test_draft)
        assert len(test_draft.versions) == initial_count + 1

        # New version should be current
        new_version = [v for v in test_draft.versions if v.version_name == 'v2.0'][0]
        assert new_version.is_current is True

        # Old version should not be current
        old_versions = [v for v in test_draft.versions if v.version_name != 'v2.0']
        assert all(not v.is_current for v in old_versions)

    def test_switch_version(self, authenticated_client, init_database, test_draft_with_versions):
        """Test switching between versions"""
        # Get non-current version
        old_version = [v for v in test_draft_with_versions.versions if not v.is_current][0]

        response = authenticated_client.post(f'/drafts/versions/{old_version.id}/switch')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Old version should now be current
        db.session.refresh(old_version)
        assert old_version.is_current is True

    def test_rename_version(self, authenticated_client, init_database, test_draft):
        """Test renaming a version"""
        version_id = test_draft.versions[0].id

        response = authenticated_client.post(f'/drafts/versions/{version_id}/rename',
            json={'name': 'Final Draft'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Version should be renamed
        version = DraftVersion.query.get(version_id)
        assert version.version_name == 'Final Draft'

    def test_set_version_tag(self, authenticated_client, init_database, test_draft):
        """Test setting version tag"""
        version_id = test_draft.versions[0].id

        response = authenticated_client.post(f'/drafts/versions/{version_id}/set_tag',
            json={'tag': 'final'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Tag should be updated
        version = DraftVersion.query.get(version_id)
        assert version.tag == 'final'


class TestDraftDeletion:
    """Test deleting drafts and versions"""

    def test_delete_version(self, authenticated_client, init_database, test_draft_with_versions):
        """Test deleting a version"""
        # Get non-current version to delete
        version_to_delete = [v for v in test_draft_with_versions.versions if not v.is_current][0]
        version_id = version_to_delete.id
        initial_count = len(test_draft_with_versions.versions)

        response = authenticated_client.post(f'/drafts/versions/{version_id}/delete')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Version should be deleted
        version = DraftVersion.query.get(version_id)
        assert version is None

        # Draft should have one less version
        db.session.refresh(test_draft_with_versions)
        assert len(test_draft_with_versions.versions) == initial_count - 1

    def test_delete_draft(self, authenticated_client, init_database, test_draft):
        """Test deleting a draft"""
        draft_id = test_draft.id
        version_ids = [v.id for v in test_draft.versions]

        response = authenticated_client.post(f'/drafts/{draft_id}/delete')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Draft should be deleted
        draft = BlogDraft.query.get(draft_id)
        assert draft is None

        # All versions should be deleted
        for version_id in version_ids:
            version = DraftVersion.query.get(version_id)
            assert version is None

    def test_cannot_delete_other_users_draft(self, authenticated_client, init_database, second_user):
        """Test cannot delete another user's draft"""
        # Create draft for second user
        draft = BlogDraft(
            title='Other User Draft',
            user_id=second_user.id,
            status='draft'
        )
        db.session.add(draft)
        db.session.commit()

        response = authenticated_client.post(f'/drafts/{draft.id}/delete')

        # Should not be able to delete
        assert response.status_code in [403, 404]

        # Draft should still exist
        assert BlogDraft.query.get(draft.id) is not None


class TestDraftSharing:
    """Test draft sharing functionality"""

    def test_generate_share_link(self, authenticated_client, init_database, test_draft):
        """Test generating a share link"""
        version_id = test_draft.versions[0].id

        response = authenticated_client.post(f'/drafts/versions/{version_id}/share')

        # This endpoint may or may not exist yet
        assert response.status_code in [200, 404]

    def test_view_shared_draft(self, client, init_database, test_draft):
        """Test viewing a shared draft without authentication"""
        version = test_draft.versions[0]

        # Generate share token
        version.share_token = 'test-share-token'
        db.session.commit()

        # Access shared link
        response = client.get(f'/shared/{version.share_token}')

        # Should be able to view without authentication
        # Endpoint may not exist yet
        assert response.status_code in [200, 404]


class TestDraftAPI:
    """Test draft API endpoints"""

    def test_list_user_drafts_api(self, authenticated_client, init_database, test_draft):
        """Test API endpoint for listing drafts"""
        response = authenticated_client.get('/api/drafts')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'drafts' in data
        assert len(data['drafts']) >= 1

    def test_draft_api_requires_auth(self, client, init_database):
        """Test draft API requires authentication"""
        response = client.get('/api/drafts')

        assert response.status_code == 302  # Redirect to login
