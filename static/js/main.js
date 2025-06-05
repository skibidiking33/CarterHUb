// Main JavaScript functionality for CarterHub

document.addEventListener('DOMContentLoaded', function() {
    // Initialize any necessary functionality
    console.log('CarterHub loaded successfully!');
    
    // Add smooth transitions to assignment cards
    const assignmentCards = document.querySelectorAll('.assignment-card');
    assignmentCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Remove problematic loading states that cause infinite loading
    // Forms will submit normally without button state changes
});

// Utility function to show notifications
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Function to handle admin form submissions
function handleAdminForm() {
    // Forms submit normally without modifications
    console.log('Admin forms ready');
}

// Initialize admin functionality if on admin page
if (window.location.pathname.includes('admin')) {
    document.addEventListener('DOMContentLoaded', handleAdminForm);
}

// Function to confirm deletions
function confirmDelete(message = 'Are you sure you want to delete this item?') {
    return confirm(message);
}

// Function to handle responsive navigation
function handleResponsiveNav() {
    const navToggle = document.querySelector('.navbar-toggler');
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            const navCollapse = document.querySelector('.navbar-collapse');
            if (navCollapse) {
                navCollapse.classList.toggle('show');
            }
        });
    }
}

// Initialize responsive navigation
document.addEventListener('DOMContentLoaded', handleResponsiveNav);
