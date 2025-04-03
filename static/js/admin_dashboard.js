// ======================
// Admin Dashboard UI Controller
// ======================
const adminUI = {
    // Initialize all functionality
    init: function() {
        this.setupResetForm();
        this.setupTickerInput();
        this.setupEventListeners();
    },

    // Setup password reset form functionality
    setupResetForm: function() {
        this.resetFormContainer = document.getElementById('resetFormContainer');
        this.resetForm = document.getElementById('resetForm');
        this.resetUserId = document.getElementById('resetUserId');
    },

    // Setup ticker input auto-uppercase
    setupTickerInput: function() {
        const tickerInput = document.getElementById('ticker');
        if (tickerInput) {
            tickerInput.addEventListener('input', function() {
                this.value = this.value.toUpperCase();
            });
        }
    },

    // General event listeners
    setupEventListeners: function() {
        // Add any additional event listeners here
    },

    // Show the password reset form
    showResetForm: function(userId) {
        this.resetUserId.value = userId;
        this.resetForm.action = `/admin/reset_password/${userId}`;
        this.resetFormContainer.classList.remove('hidden');
    },

    // Hide the password reset form
    hideResetForm: function() {
        this.resetFormContainer.classList.add('hidden');
        this.resetForm.reset();
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    adminUI.init();
});