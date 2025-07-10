// Editor JavaScript Module
class DraftEditor {
    constructor() {
        this.data = null;
        this.autoSaveTimeout = null;
        this.lastSavedContent = '';
        this.pendingTag = null;
        
        this.init();
    }
    
    init() {
        // Load editor data
        this.loadEditorData();
        
        // Initialize components
        this.initElements();
        this.initEventListeners();
        this.initWindowControls();
        this.loadDraftsList();
        
        // Initialize content
        this.updateWordCount();
        this.updateSaveStatus('Ready', 'ready');
        this.lastSavedContent = this.elements.contentEditor.value;
        
        // Auto-resize textarea
        this.initAutoResize();
    }
    
    loadEditorData() {
        const dataElement = document.getElementById('editorData');
        if (dataElement) {
            this.data = JSON.parse(dataElement.textContent);
        }
    }
    
    initElements() {
        this.elements = {
            // Editor elements
            contentEditor: document.getElementById('contentEditor'),
            wordCount: document.getElementById('wordCount'),
            saveIndicator: document.getElementById('saveIndicator'),
            saveStatus: document.getElementById('saveStatus'),
            draftTitle: document.getElementById('draftTitle'),
            versionName: document.getElementById('versionName'),
            
            // Sidebar elements
            draftsList: document.getElementById('draftsList'),
            
            // Action buttons
            saveBtn: document.getElementById('saveBtn'),
            previewBtn: document.getElementById('previewBtn'),
            newVersionBtn: document.getElementById('newVersionBtn'),
            compareBtn: document.getElementById('compareBtn'),
            shareBtn: document.getElementById('shareBtn'),
            exportBtn: document.getElementById('exportBtn'),
            
            // Modals
            newVersionModal: document.getElementById('newVersionModal'),
            compareModal: document.getElementById('compareModal'),
            shareModal: document.getElementById('shareModal'),
            previewModal: document.getElementById('previewModal'),
            
            // Modal content
            newVersionName: document.getElementById('newVersionName'),
            compareVersion: document.getElementById('compareVersion'),
            shareLink: document.getElementById('shareLink'),
            shareLinkContainer: document.getElementById('shareLinkContainer'),
            previewContent: document.getElementById('previewContent'),
            
            // Window controls
            editorClose: document.getElementById('editorClose'),
            editorMinimize: document.getElementById('editorMinimize'),
            editorMaximize: document.getElementById('editorMaximize'),
            editorContainer: document.getElementById('editorContainer')
        };
    }
    
    initEventListeners() {
        // Content editor
        this.elements.contentEditor.addEventListener('input', () => {
            this.handleContentChange();
        });
        
        // Save button
        this.elements.saveBtn.addEventListener('click', () => {
            this.saveContent();
        });
        
        // Action buttons
        this.elements.previewBtn.addEventListener('click', () => {
            this.showPreview();
        });
        
        this.elements.newVersionBtn.addEventListener('click', () => {
            this.showModal('newVersionModal');
        });
        
        this.elements.compareBtn.addEventListener('click', () => {
            this.showModal('compareModal');
        });
        
        this.elements.shareBtn.addEventListener('click', () => {
            this.showModal('shareModal');
        });
        
        this.elements.exportBtn.addEventListener('click', () => {
            this.exportMarkdown();
        });
        
        // Modal handlers
        this.initModalHandlers();
        
        // Tag buttons
        this.initTagButtons();
        
        // Editable metadata
        this.initEditableMetadata();
        
        // Keyboard shortcuts
        this.initKeyboardShortcuts();
    }
    
    initModalHandlers() {
        // New Version Modal
        document.getElementById('closeNewVersionModal').addEventListener('click', () => {
            this.hideModal('newVersionModal');
        });
        
        document.getElementById('cancelNewVersion').addEventListener('click', () => {
            this.hideModal('newVersionModal');
        });
        
        document.getElementById('createVersion').addEventListener('click', () => {
            this.createNewVersion();
        });
        
        // Compare Modal
        document.getElementById('closeCompareModal').addEventListener('click', () => {
            this.hideModal('compareModal');
        });
        
        document.getElementById('cancelCompare').addEventListener('click', () => {
            this.hideModal('compareModal');
        });
        
        document.getElementById('executeCompare').addEventListener('click', () => {
            this.executeCompare();
        });
        
        // Share Modal
        document.getElementById('closeShareModal').addEventListener('click', () => {
            this.hideModal('shareModal');
        });
        
        document.getElementById('cancelShare').addEventListener('click', () => {
            this.hideModal('shareModal');
        });
        
        document.getElementById('generateShareLink').addEventListener('click', () => {
            this.generateShareLink();
        });
        
        document.getElementById('copyShareLink').addEventListener('click', () => {
            this.copyShareLink();
        });
        
        // Preview Modal
        document.getElementById('closePreviewModal').addEventListener('click', () => {
            this.hideModal('previewModal');
        });
        
        document.getElementById('closePreview').addEventListener('click', () => {
            this.hideModal('previewModal');
        });
        
        // Close modals on outside click
        document.querySelectorAll('.modal-overlay').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });
        });
    }
    
    initTagButtons() {
        document.querySelectorAll('.tag-btn[data-tag]').forEach(btn => {
            btn.addEventListener('click', () => {
                const newTag = btn.dataset.tag;
                this.setVersionTag(newTag);
            });
        });
    }
    
    initEditableMetadata() {
        this.elements.draftTitle.addEventListener('click', () => {
            this.editMetadata('draft', this.elements.draftTitle);
        });
        
        this.elements.versionName.addEventListener('click', () => {
            this.editMetadata('version', this.elements.versionName);
        });
    }
    
    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 's':
                        e.preventDefault();
                        this.saveContent();
                        break;
                    case 'n':
                        e.preventDefault();
                        this.showModal('newVersionModal');
                        break;
                    case 'p':
                        e.preventDefault();
                        this.showPreview();
                        break;
                }
            }
            
            if (e.key === 'Escape') {
                // Close any open modals
                document.querySelectorAll('.modal-overlay').forEach(modal => {
                    modal.style.display = 'none';
                });
            }
        });
    }
    
    initWindowControls() {
        this.elements.editorClose.addEventListener('click', () => {
            if (confirm('Close editor? Any unsaved changes will be lost.')) {
                window.location.href = '/dashboard';
            }
        });
        
        this.elements.editorMinimize.addEventListener('click', () => {
            const container = this.elements.editorContainer;
            if (container.style.transform === 'scale(0.1)') {
                container.style.transform = 'scale(1)';
                container.style.opacity = '1';
            } else {
                container.style.transform = 'scale(0.1)';
                container.style.opacity = '0.3';
            }
            container.style.transition = 'all 0.3s ease';
        });
        
        this.elements.editorMaximize.addEventListener('click', () => {
            const layout = document.querySelector('.editor-layout');
            const isMaximized = layout.getAttribute('data-maximized') === 'true';
            
            if (!isMaximized) {
                // Store original styles
                layout.setAttribute('data-original-position', layout.style.position || '');
                layout.setAttribute('data-original-top', layout.style.top || '');
                layout.setAttribute('data-original-left', layout.style.left || '');
                layout.setAttribute('data-original-right', layout.style.right || '');
                layout.setAttribute('data-original-bottom', layout.style.bottom || '');
                layout.setAttribute('data-original-z-index', layout.style.zIndex || '');
                layout.setAttribute('data-original-margin', layout.style.margin || '');
                
                // Maximize
                layout.style.position = 'fixed';
                layout.style.top = '0';
                layout.style.left = '0';
                layout.style.right = '0';
                layout.style.bottom = '0';
                layout.style.zIndex = '999';
                layout.style.margin = '0';
                layout.style.transition = 'all 0.3s ease';
                layout.setAttribute('data-maximized', 'true');
            } else {
                // Restore
                layout.style.position = layout.getAttribute('data-original-position');
                layout.style.top = layout.getAttribute('data-original-top');
                layout.style.left = layout.getAttribute('data-original-left');
                layout.style.right = layout.getAttribute('data-original-right');
                layout.style.bottom = layout.getAttribute('data-original-bottom');
                layout.style.zIndex = layout.getAttribute('data-original-z-index');
                layout.style.margin = layout.getAttribute('data-original-margin');
                layout.setAttribute('data-maximized', 'false');
            }
        });
    }
    
    initAutoResize() {
        const textarea = this.elements.contentEditor;
        
        const autoResize = () => {
            // Reset height to auto to get the scroll height
            textarea.style.height = 'auto';
            // Set height to scroll height with minimum of 400px
            textarea.style.height = Math.max(400, textarea.scrollHeight) + 'px';
        };
        
        textarea.addEventListener('input', autoResize);
        // Initial resize
        setTimeout(autoResize, 100);
    }
    
    handleContentChange() {
        clearTimeout(this.autoSaveTimeout);
        this.autoSaveTimeout = setTimeout(() => {
            this.autoSave();
        }, 2000);
        
        this.updateWordCount();
    }
    
    updateWordCount() {
        const content = this.elements.contentEditor.value;
        const words = content.trim().split(/\s+/).filter(word => word.length > 0).length;
        this.elements.wordCount.textContent = words;
    }
    
    updateSaveStatus(status, type = 'ready') {
        const indicator = this.elements.saveIndicator;
        const statusText = this.elements.saveStatus;
        
        indicator.className = 'status-dot';
        if (type === 'saving') indicator.classList.add('saving');
        if (type === 'error') indicator.classList.add('error');
        
        statusText.textContent = status;
    }
    
    async saveContent() {
        const content = this.elements.contentEditor.value;
        this.updateSaveStatus('Saving...', 'saving');
        
        try {
            const response = await fetch(`/drafts/versions/${this.data.currentVersionId}/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: content })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.lastSavedContent = content;
                this.updateSaveStatus('Saved', 'ready');
                return true;
            } else {
                this.updateSaveStatus('Failed', 'error');
                return false;
            }
        } catch (error) {
            this.updateSaveStatus('Failed', 'error');
            return false;
        }
    }
    
    async autoSave() {
        const content = this.elements.contentEditor.value;
        if (content !== this.lastSavedContent) {
            await this.saveContent();
        }
    }
    
    showModal(modalId) {
        this.elements[modalId].style.display = 'block';
        
        // Focus on first input if available
        const firstInput = this.elements[modalId].querySelector('input, textarea, select');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }
    
    hideModal(modalId) {
        this.elements[modalId].style.display = 'none';
        
        // Clear form data
        const form = this.elements[modalId].querySelector('form');
        if (form) {
            form.reset();
        }
    }
    
    async loadDraftsList() {
        try {
            const response = await fetch('/api/drafts');
            const data = await response.json();
            
            this.renderDraftsList(data.drafts);
        } catch (error) {
            console.error('Failed to load drafts list:', error);
        }
    }
    
    renderDraftsList(drafts) {
        const container = this.elements.draftsList;
        container.innerHTML = '';
        
        drafts.forEach(draft => {
            const draftItem = document.createElement('div');
            draftItem.className = 'draft-item';
            
            const isCurrentDraft = draft.id === this.data.draftId;
            
            const draftLink = document.createElement('a');
            draftLink.className = `draft-link ${isCurrentDraft ? 'active' : ''}`;
            draftLink.href = `/drafts/${draft.id}`;
            
            const draftText = document.createElement('span');
            draftText.className = 'draft-link-text';
            draftText.textContent = draft.title;
            draftLink.appendChild(draftText);
            
            draftItem.appendChild(draftLink);
            
            // If this is the current draft, show versions
            if (isCurrentDraft && this.data.versions) {
                const versionsList = document.createElement('ul');
                versionsList.className = 'version-list';
                
                this.data.versions.forEach(version => {
                    const versionItem = document.createElement('li');
                    versionItem.className = 'version-item';
                    
                    const versionLink = document.createElement('a');
                    versionLink.className = `version-link ${version.id === this.data.currentVersionId ? 'active' : ''}`;
                    versionLink.href = `/drafts/${draft.id}?version=${version.id}`;
                    
                    const versionText = document.createElement('span');
                    versionText.className = 'version-link-text';
                    versionText.textContent = version.version_name;
                    versionLink.appendChild(versionText);
                    
                    // Add version tag if not draft
                    if (version.tag && version.tag !== 'draft') {
                        const versionTag = document.createElement('span');
                        versionTag.className = `version-tag ${version.tag}`;
                        
                        const tagText = {
                            'final': 'FINAL',
                            'ready_for_review': 'REVIEW',
                            'working': 'WORK'
                        }[version.tag] || version.tag.toUpperCase();
                        
                        versionTag.textContent = tagText;
                        versionLink.appendChild(versionTag);
                    }
                    
                    versionItem.appendChild(versionLink);
                    versionsList.appendChild(versionItem);
                });
                
                draftItem.appendChild(versionsList);
            }
            
            container.appendChild(draftItem);
        });
    }
    
    async createNewVersion() {
        const versionName = this.elements.newVersionName.value.trim();
        if (!versionName) {
            alert('Please enter a version name');
            return;
        }
        
        const content = this.elements.contentEditor.value;
        const formData = new FormData();
        formData.append('version_name', versionName);
        formData.append('content', content);
        
        try {
            const response = await fetch(`/drafts/${this.data.draftId}/versions`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                location.reload();
            } else {
                alert('Failed to create version');
            }
        } catch (error) {
            alert('Failed to create version');
        }
    }
    
    executeCompare() {
        const compareVersionId = this.elements.compareVersion.value;
        if (compareVersionId) {
            window.open(`/drafts/compare/${this.data.currentVersionId}/${compareVersionId}`, '_blank');
            this.hideModal('compareModal');
        } else {
            alert('Please select a version to compare against');
        }
    }
    
    async generateShareLink() {
        try {
            const response = await fetch(`/drafts/versions/${this.data.currentVersionId}/share`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.elements.shareLink.textContent = data.share_url;
                this.elements.shareLinkContainer.style.display = 'block';
                document.getElementById('copyShareLink').style.display = 'inline-block';
            } else {
                alert('Failed to generate share link');
            }
        } catch (error) {
            alert('Failed to generate share link');
        }
    }
    
    async copyShareLink() {
        const shareLink = this.elements.shareLink.textContent;
        try {
            await navigator.clipboard.writeText(shareLink);
            const btn = document.getElementById('copyShareLink');
            const originalText = btn.textContent;
            btn.textContent = 'Copied!';
            setTimeout(() => {
                btn.textContent = originalText;
            }, 2000);
        } catch (error) {
            alert('Failed to copy link to clipboard');
        }
    }
    
    async showPreview() {
        const content = this.elements.contentEditor.value;
        
        try {
            const response = await fetch(`/drafts/versions/${this.data.currentVersionId}/preview`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: content })
            });
            
            const data = await response.json();
            
            this.elements.previewContent.innerHTML = data.html;
            this.showModal('previewModal');
        } catch (error) {
            this.elements.previewContent.innerHTML = '<p style="color: var(--accent-red);">Preview unavailable</p>';
            this.showModal('previewModal');
        }
    }
    
    exportMarkdown() {
        const content = this.elements.contentEditor.value;
        const blob = new Blob([content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.data.draft.title}.md`;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    async setVersionTag(tag) {
        try {
            const response = await fetch(`/drafts/versions/${this.data.currentVersionId}/set_tag`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tag: tag })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update UI
                document.querySelectorAll('.tag-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                document.querySelector(`[data-tag="${tag}"]`).classList.add('active');
            } else {
                alert('Failed to update version status');
            }
        } catch (error) {
            alert('Failed to update version status');
        }
    }
    
    editMetadata(type, element) {
        const currentValue = element.textContent;
        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentValue;
        input.className = 'metadata-value editing';
        
        element.parentNode.replaceChild(input, element);
        input.focus();
        input.select();
        
        const saveEdit = async () => {
            const newValue = input.value.trim();
            if (!newValue || newValue === currentValue) {
                input.parentNode.replaceChild(element, input);
                return;
            }
            
            try {
                let endpoint, payload;
                
                if (type === 'draft') {
                    endpoint = `/drafts/${this.data.draftId}/rename`;
                    payload = { name: newValue };
                } else {
                    endpoint = `/drafts/versions/${this.data.currentVersionId}/rename`;
                    payload = { name: newValue };
                }
                
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    element.textContent = newValue;
                    input.parentNode.replaceChild(element, input);
                    
                    // Update data
                    if (type === 'draft') {
                        this.data.draft.title = newValue;
                    } else {
                        this.data.currentVersion.version_name = newValue;
                    }
                } else {
                    alert('Failed to update name');
                    input.parentNode.replaceChild(element, input);
                }
            } catch (error) {
                alert('Failed to update name');
                input.parentNode.replaceChild(element, input);
            }
        };
        
        input.addEventListener('blur', saveEdit);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                saveEdit();
            } else if (e.key === 'Escape') {
                input.parentNode.replaceChild(element, input);
            }
        });
    }
}

// Initialize editor when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DraftEditor();
});