// Teacher Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    initTabs();

    // Auto-hide messages
    initMessages();

    // Mobile menu toggle (if needed)
    initMobileMenu();

    // Init tooltips and popovers
    initTooltips();
});

/**
 * Initialize tab switching
 */
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    if (tabButtons.length === 0) return;

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active from all
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active to clicked
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            const targetContent = document.getElementById(tabId);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });
}

/**
 * Initialize message auto-hide
 */
function initMessages() {
    const messagesContainer = document.querySelector('.messages-container');
    if (!messagesContainer) return;

    // Auto-hide after 5 seconds
    setTimeout(() => {
        const alerts = messagesContainer.querySelectorAll('.alert');
        alerts.forEach(alert => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease';
            setTimeout(() => alert.remove(), 500);
        });
    }, 5000);

    // Close button functionality
    const closeButtons = document.querySelectorAll('.close-alert');
    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            const alert = button.parentElement;
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease';
            setTimeout(() => alert.remove(), 500);
        });
    });
}

/**
 * Initialize mobile menu toggle
 */
function initMobileMenu() {
    const menuToggle = document.querySelector('.menu-toggle');
    const sidebar = document.querySelector('.sidebar');

    if (!menuToggle || !sidebar) return;

    menuToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
    });
}

/**
 * Initialize tooltips (simple implementation)
 */
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');

    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(event) {
    const text = event.target.getAttribute('data-tooltip');
    if (!text) return;

    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-size: 0.875rem;
        pointer-events: none;
        z-index: 10000;
        white-space: nowrap;
    `;

    document.body.appendChild(tooltip);

    const rect = event.target.getBoundingClientRect();
    tooltip.style.left = `${rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2)}px`;
    tooltip.style.top = `${rect.top - tooltip.offsetHeight - 8}px`;

    event.target._tooltip = tooltip;
}

function hideTooltip(event) {
    const tooltip = event.target._tooltip;
    if (tooltip) {
        tooltip.remove();
        delete event.target._tooltip;
    }
}

/**
 * Confirmation dialogs
 */
function confirmAction(message) {
    return confirm(message);
}

/**
 * Format date helpers
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ro-RO', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatTime(timeString) {
    return timeString;
}

/**
 * Loading state helpers
 */
function showLoading(element) {
    element.classList.add('loading');
    element.disabled = true;
}

function hideLoading(element) {
    element.classList.remove('loading');
    element.disabled = false;
}

/**
 * Export functions for global use
 */
window.confirmAction = confirmAction;
window.formatDate = formatDate;
window.formatTime = formatTime;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
