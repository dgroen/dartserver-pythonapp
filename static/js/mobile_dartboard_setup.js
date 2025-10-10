// Mobile Dartboard Setup JavaScript

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('dartboardSetupForm').addEventListener('submit', registerDartboard);
    document.getElementById('generateIdBtn').addEventListener('click', generateDartboardId);
    document.getElementById('generateKeyBtn').addEventListener('click', generateWpaKey);
});

async function registerDartboard(e) {
    e.preventDefault();
    
    const dartboardId = document.getElementById('dartboardId').value;
    const wpaKey = document.getElementById('wpaKey').value;
    const name = document.getElementById('dartboardName').value;
    
    if (!dartboardId || !wpaKey) {
        showAlert('Please fill in Dartboard ID and WPA Key', 'error');
        return;
    }
    
    try {
        await apiRequest('/api/mobile/dartboards', {
            method: 'POST',
            body: JSON.stringify({
                dartboard_id: dartboardId,
                wpa_key: wpaKey,
                name: name || null
            })
        });
        
        showAlert('Dartboard registered successfully!', 'success');
        
        // Redirect to account page after 2 seconds
        setTimeout(() => {
            window.location.href = '/mobile/account';
        }, 2000);
    } catch (error) {
        console.error('Failed to register dartboard:', error);
        showAlert('Failed to register dartboard: ' + error.message, 'error');
    }
}

function generateDartboardId() {
    // Generate a unique dartboard ID (e.g., DART-XXXX)
    const randomPart = Math.random().toString(36).substring(2, 8).toUpperCase();
    const dartboardId = `DART-${randomPart}`;
    document.getElementById('dartboardId').value = dartboardId;
}

function generateWpaKey() {
    // Generate a random WPA key (8-63 characters)
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let wpaKey = '';
    for (let i = 0; i < 16; i++) {
        wpaKey += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    document.getElementById('wpaKey').value = wpaKey;
}