// Mobile Hotspot Control JavaScript

document.addEventListener('DOMContentLoaded', () => {
    loadHotspotConfig();
    detectPlatform();
    
    document.getElementById('hotspotConfigForm').addEventListener('submit', saveHotspotConfig);
    document.getElementById('toggleHotspotBtn').addEventListener('click', toggleHotspot);
});

let currentConfig = null;

async function loadHotspotConfig() {
    try {
        const data = await apiRequest('/api/mobile/hotspot');
        currentConfig = data.config;
        displayHotspotConfig(data.config);
    } catch (error) {
        console.error('Failed to load hotspot config:', error);
        showAlert('Failed to load hotspot configuration', 'error');
    }
}

function displayHotspotConfig(config) {
    if (!config) {
        document.getElementById('currentConfig').innerHTML = '<p class="empty-state">No hotspot configured</p>';
        document.getElementById('toggleHotspotBtn').disabled = true;
        return;
    }
    
    document.getElementById('dartboardId').value = config.dartboard_id;
    document.getElementById('wpaKey').value = config.wpa_key;
    
    document.getElementById('currentConfig').innerHTML = `
        <div class="item">
            <div class="item-info">
                <div class="item-title">SSID: ${config.dartboard_id}</div>
                <div class="item-subtitle">WPA Key: ${config.wpa_key}</div>
                <div class="item-subtitle">
                    ${config.is_active ? '<span class="status-badge status-connected">Active</span>' : '<span class="status-badge status-disconnected">Inactive</span>'}
                </div>
            </div>
        </div>
    `;
    
    const toggleBtn = document.getElementById('toggleHotspotBtn');
    toggleBtn.disabled = false;
    toggleBtn.textContent = config.is_active ? 'Deactivate Hotspot' : 'Activate Hotspot';
    toggleBtn.className = config.is_active ? 'btn btn-warning btn-large' : 'btn btn-success btn-large';
}

async function saveHotspotConfig(e) {
    e.preventDefault();
    
    const dartboardId = document.getElementById('dartboardId').value;
    const wpaKey = document.getElementById('wpaKey').value;
    
    if (!dartboardId || !wpaKey) {
        showAlert('Please fill in all fields', 'error');
        return;
    }
    
    try {
        await apiRequest('/api/mobile/hotspot', {
            method: 'POST',
            body: JSON.stringify({
                dartboard_id: dartboardId,
                wpa_key: wpaKey
            })
        });
        
        loadHotspotConfig();
        showAlert('Hotspot configuration saved', 'success');
    } catch (error) {
        console.error('Failed to save hotspot config:', error);
        showAlert('Failed to save hotspot configuration', 'error');
    }
}

async function toggleHotspot() {
    if (!currentConfig) {
        showAlert('Please configure hotspot first', 'error');
        return;
    }
    
    try {
        const data = await apiRequest('/api/mobile/hotspot/toggle', {
            method: 'POST'
        });
        
        currentConfig = data.config;
        displayHotspotConfig(data.config);
        
        if (data.config.is_active) {
            showAlert('Hotspot activated. Please create the hotspot manually on your device.', 'success');
        } else {
            showAlert('Hotspot deactivated', 'success');
        }
    } catch (error) {
        console.error('Failed to toggle hotspot:', error);
        showAlert('Failed to toggle hotspot', 'error');
    }
}

function detectPlatform() {
    const userAgent = navigator.userAgent || navigator.vendor || window.opera;
    
    let platform = 'unknown';
    if (/android/i.test(userAgent)) {
        platform = 'android';
    } else if (/iPad|iPhone|iPod/.test(userAgent) && !window.MSStream) {
        platform = 'ios';
    }
    
    // Show platform-specific instructions
    document.querySelectorAll('.instructions').forEach(el => {
        if (el.dataset.platform === platform) {
            el.style.display = 'block';
        } else {
            el.style.display = 'none';
        }
    });
    
    // If no specific platform detected, show all
    if (platform === 'unknown') {
        document.querySelectorAll('.instructions').forEach(el => {
            el.style.display = 'block';
        });
    }
}