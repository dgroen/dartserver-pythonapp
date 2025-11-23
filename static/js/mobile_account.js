// Mobile Account Management JavaScript

document.addEventListener('DOMContentLoaded', () => {
    loadApiKeys();
    loadDartboards();

    document.getElementById('generateApiKeyBtn').addEventListener('click', generateApiKey);
    document.getElementById('addDartboardBtn').addEventListener('click', () => {
        window.location.href = '/mobile/dartboard-setup';
    });
});

// API Keys Management
async function loadApiKeys() {
    try {
        const data = await apiRequest('/api/mobile/apikeys');
        displayApiKeys(data.api_keys);
    } catch (error) {
        console.error('Failed to load API keys:', error);
        showAlert('Failed to load API keys', 'error');
    }
}

function displayApiKeys(apiKeys) {
    const container = document.getElementById('apiKeysList');

    if (apiKeys.length === 0) {
        container.innerHTML = '<p class="empty-state">No API keys generated</p>';
        return;
    }

    container.innerHTML = apiKeys.map(key => `
        <div class="item">
            <div class="item-info">
                <div class="item-title">${key.name || 'API Key'}</div>
                <div class="item-subtitle">
                    ${key.key_prefix}...
                    ${key.is_active ? '<span class="status-badge status-connected">Active</span>' : '<span class="status-badge status-disconnected">Revoked</span>'}
                </div>
                <div class="item-subtitle">Created: ${formatDate(key.created_at)}</div>
                ${key.last_used_at ? `<div class="item-subtitle">Last used: ${formatDate(key.last_used_at)}</div>` : ''}
            </div>
            <div class="item-actions">
                ${key.is_active ? `<button class="btn btn-small btn-danger" onclick="revokeApiKey(${key.id})">Revoke</button>` : ''}
                <button class="btn btn-small btn-secondary" onclick="deleteApiKey(${key.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

async function generateApiKey() {
    const name = prompt('Enter a name for this API key (optional):');

    try {
        const data = await apiRequest('/api/mobile/apikeys', {
            method: 'POST',
            body: JSON.stringify({ name: name || 'Mobile API Key' })
        });

        // Show the full key (only time it's visible)
        alert(`API Key Generated:\n\n${data.api_key}\n\nSave this key securely. You won't be able to see it again!`);

        loadApiKeys();
        showAlert('API key generated successfully', 'success');
    } catch (error) {
        console.error('Failed to generate API key:', error);
        showAlert('Failed to generate API key', 'error');
    }
}

async function revokeApiKey(keyId) {
    if (!confirm('Are you sure you want to revoke this API key?')) {
        return;
    }

    try {
        await apiRequest(`/api/mobile/apikeys/${keyId}/revoke`, {
            method: 'POST'
        });

        loadApiKeys();
        showAlert('API key revoked', 'success');
    } catch (error) {
        console.error('Failed to revoke API key:', error);
        showAlert('Failed to revoke API key', 'error');
    }
}

async function deleteApiKey(keyId) {
    if (!confirm('Are you sure you want to delete this API key?')) {
        return;
    }

    try {
        await apiRequest(`/api/mobile/apikeys/${keyId}`, {
            method: 'DELETE'
        });

        loadApiKeys();
        showAlert('API key deleted', 'success');
    } catch (error) {
        console.error('Failed to delete API key:', error);
        showAlert('Failed to delete API key', 'error');
    }
}

// Dartboards Management
async function loadDartboards() {
    try {
        const data = await apiRequest('/api/mobile/dartboards');
        displayDartboards(data.dartboards);
    } catch (error) {
        console.error('Failed to load dartboards:', error);
        showAlert('Failed to load dartboards', 'error');
    }
}

function displayDartboards(dartboards) {
    const container = document.getElementById('dartboardsList');

    if (dartboards.length === 0) {
        container.innerHTML = '<p class="empty-state">No dartboards registered</p>';
        return;
    }

    container.innerHTML = dartboards.map(board => `
        <div class="item">
            <div class="item-info">
                <div class="item-title">${board.name || board.dartboard_id}</div>
                <div class="item-subtitle">
                    ID: ${board.dartboard_id}
                    ${board.is_connected ? '<span class="status-badge status-connected">Connected</span>' : '<span class="status-badge status-disconnected">Disconnected</span>'}
                </div>
                ${board.last_connected_at ? `<div class="item-subtitle">Last connected: ${formatDate(board.last_connected_at)}</div>` : ''}
            </div>
            <div class="item-actions">
                <button class="btn btn-small btn-secondary" onclick="deleteDartboard(${board.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

async function deleteDartboard(boardId) {
    if (!confirm('Are you sure you want to delete this dartboard?')) {
        return;
    }

    try {
        await apiRequest(`/api/mobile/dartboards/${boardId}`, {
            method: 'DELETE'
        });

        loadDartboards();
        showAlert('Dartboard deleted', 'success');
    } catch (error) {
        console.error('Failed to delete dartboard:', error);
        showAlert('Failed to delete dartboard', 'error');
    }
}
