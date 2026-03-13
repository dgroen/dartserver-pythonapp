// Main JavaScript for Let's Play Darts website

document.addEventListener('DOMContentLoaded', function() {
    // Form validation and handling
    initializeForms();
    
    // Smooth scrolling for anchor links
    initializeSmoothScrolling();
    
    // Mobile menu toggle (if needed in future)
    initializeMobileMenu();
});

// Initialize form handling
function initializeForms() {
    // Registration form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegistration);
    }
    
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
}

// Handle registration form submission
function handleRegistration(e) {
    e.preventDefault();
    
    const formData = {
        username: document.getElementById('username').value,
        email: document.getElementById('email').value,
        fullname: document.getElementById('fullname').value,
        password: document.getElementById('password').value,
        confirmPassword: document.getElementById('confirmPassword').value,
        terms: document.getElementById('terms').checked
    };
    
    // Validate password match
    if (formData.password !== formData.confirmPassword) {
        showMessage('Passwords do not match!', 'error');
        return;
    }
    
    // Validate password strength
    if (formData.password.length < 8) {
        showMessage('Password must be at least 8 characters long!', 'error');
        return;
    }
    
    // Validate terms acceptance
    if (!formData.terms) {
        showMessage('You must agree to the terms of service!', 'error');
        return;
    }
    
    // In a real application, this would send data to a server
    console.log('Registration data:', formData);
    showMessage('Registration successful! Redirecting to login...', 'success');
    
    // Simulate redirect after successful registration
    setTimeout(() => {
        window.location.href = 'login.html';
    }, 2000);
}

// Handle login form submission
function handleLogin(e) {
    e.preventDefault();
    
    const formData = {
        email: document.getElementById('loginEmail').value,
        password: document.getElementById('loginPassword').value,
        remember: document.getElementById('remember').checked
    };
    
    // In a real application, this would authenticate with a server
    console.log('Login data:', formData);
    showMessage('Login successful! Redirecting to dashboard...', 'success');
    
    // Simulate redirect after successful login
    setTimeout(() => {
        // In a real app, this would redirect to the actual dashboard
        showMessage('Dashboard not yet implemented. This is a demonstration.', 'info');
    }, 2000);
}

// Show message to user
function showMessage(message, type = 'info') {
    // Remove any existing messages
    const existingMessage = document.querySelector('.message-banner');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-banner message-${type}`;
    messageDiv.textContent = message;
    
    // Add styles
    messageDiv.style.cssText = `
        position: fixed;
        top: 80px;
        left: 50%;
        transform: translateX(-50%);
        padding: 1rem 2rem;
        border-radius: 5px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        z-index: 2000;
        animation: slideDown 0.3s ease;
        max-width: 90%;
        text-align: center;
    `;
    
    // Set color based on type
    const colors = {
        success: { bg: '#2ecc71', text: '#fff' },
        error: { bg: '#e74c3c', text: '#fff' },
        info: { bg: '#3498db', text: '#fff' },
        warning: { bg: '#f39c12', text: '#fff' }
    };
    
    const color = colors[type] || colors.info;
    messageDiv.style.backgroundColor = color.bg;
    messageDiv.style.color = color.text;
    
    // Add to page
    document.body.appendChild(messageDiv);
    
    // Remove after 5 seconds
    setTimeout(() => {
        messageDiv.style.animation = 'slideUp 0.3s ease';
        setTimeout(() => messageDiv.remove(), 300);
    }, 5000);
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideDown {
        from {
            transform: translateX(-50%) translateY(-100%);
            opacity: 0;
        }
        to {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }
    }
    
    @keyframes slideUp {
        from {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }
        to {
            transform: translateX(-50%) translateY(-100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize smooth scrolling for documentation links
function initializeSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#') return;
            
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                const offsetTop = target.offsetTop - 80; // Account for fixed navbar
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Initialize mobile menu (placeholder for future enhancement)
function initializeMobileMenu() {
    // This can be expanded later if a hamburger menu is needed for mobile
    const navbar = document.querySelector('.navbar');
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        // Optional: Hide navbar on scroll down, show on scroll up
        // Uncomment if desired
        /*
        if (currentScroll > lastScroll && currentScroll > 100) {
            navbar.style.transform = 'translateY(-100%)';
        } else {
            navbar.style.transform = 'translateY(0)';
        }
        */
        
        lastScroll = currentScroll;
    });
}

// Utility function for form validation
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Export functions for testing if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        validateEmail,
        showMessage
    };
}
