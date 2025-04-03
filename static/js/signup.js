// signup.js - Handles all interactive behavior for the signup page

// ======================
// DOM Elements
// ======================
const togglePassword = document.querySelector('#togglePassword');
const passwordInput = document.querySelector('#password');
const form = document.querySelector('form');
const particlesContainer = document.getElementById('particles');
const inputs = document.querySelectorAll('input');
const loginContainer = document.querySelector('.login-container');

// ======================
// Password Visibility Toggle
// ======================
togglePassword.addEventListener('click', function() {
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    this.textContent = type === 'password' ? '👁️' : '👁️‍🗨️';
});

// ======================
// Floating Particles Effect
// ======================
function createParticles() {
    const particleCount = 15;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.classList.add('particle');
        
        // Random properties
        const size = Math.random() * 8 + 2;
        const posX = Math.random() * 100;
        const posY = Math.random() * 100;
        const duration = Math.random() * 20 + 10;
        const delay = Math.random() * -20;
        const opacity = Math.random() * 0.3 + 0.1;
        
        // Apply styles
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.left = `${posX}%`;
        particle.style.top = `${posY}%`;
        particle.style.animationDuration = `${duration}s`;
        particle.style.animationDelay = `${delay}s`;
        particle.style.opacity = opacity;
        
        particlesContainer.appendChild(particle);
    }
}

// ======================
// Input Field Effects
// ======================
function setupInputEffects() {
    inputs.forEach(input => {
        const parent = input.closest('.input-group');
        
        input.addEventListener('focus', () => {
            parent.querySelector('label').style.color = '#00ff9d';
        });
        
        input.addEventListener('blur', () => {
            parent.querySelector('label').style.color = 'var(--text-secondary)';
        });
    });
}

// ======================
// Form Submission Handler
// ======================
function handleFormSubmission() {
    form.addEventListener('submit', function(e) {
        const btn = this.querySelector('.btn');
        btn.disabled = true;
        btn.innerHTML = '<span class="animate-spin">⚡</span> Authenticating...';
    });
}

// ======================
// Login Container Hover Effect
// ======================
function setupHoverEffect() {
    loginContainer.addEventListener('mousemove', (e) => {
        const x = e.clientX - loginContainer.getBoundingClientRect().left;
        const y = e.clientY - loginContainer.getBoundingClientRect().top;
        
        loginContainer.style.setProperty('--mouse-x', `${x}px`);
        loginContainer.style.setProperty('--mouse-y', `${y}px`);
    });
}

// ======================
// Initialize Everything
// ======================
document.addEventListener('DOMContentLoaded', function() {
    createParticles();
    setupInputEffects();
    handleFormSubmission();
    setupHoverEffect();
});