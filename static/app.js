/**
 * Bharatam AI - Frontend Application
 * Handles conversation flow and UI interactions
 */

// Configuration
const API_BASE_URL = 'http://127.0.0.1:8000';

// State
let sessionId = null;
let currentLanguage = 'en';

// DOM Elements
const messagesContainer = document.getElementById('messages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const languageSelect = document.getElementById('language');
const schemesContainer = document.getElementById('schemesContainer');
const schemesList = document.getElementById('schemesList');
const loadingIndicator = document.getElementById('loading');
const chatContainer = document.getElementById('chatContainer');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
});

/**
 * Initialize the application
 */
async function initializeApp() {
    try {
        await startConversation();
    } catch (error) {
        showError('Failed to start conversation. Please refresh the page.');
        console.error('Initialization error:', error);
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Send button click
    sendButton.addEventListener('click', handleSendMessage);
    
    // Enter key press
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
    
    // Language change
    languageSelect.addEventListener('change', handleLanguageChange);
}

/**
 * Start a new conversation
 */
async function startConversation() {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/conversation/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                language: currentLanguage
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to start conversation');
        }
        
        const data = await response.json();
        sessionId = data.session_id;
        
        // Display greeting
        addMessage('assistant', data.greeting);
        
    } catch (error) {
        showError('Failed to connect to server. Please check if the API is running.');
        console.error('Start conversation error:', error);
    } finally {
        showLoading(false);
    }
}

/**
 * Handle sending a message
 */
async function handleSendMessage() {
    const message = messageInput.value.trim();
    
    if (!message || !sessionId) {
        return;
    }
    
    // Disable input while processing
    setInputEnabled(false);
    
    // Add user message to UI
    addMessage('user', message);
    messageInput.value = '';
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/conversation/${sessionId}/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to send message');
        }
        
        const data = await response.json();
        
        // Add assistant response
        addMessage('assistant', data.response);
        
        // Display eligible schemes if available
        if (data.eligible_schemes && data.eligible_schemes.length > 0) {
            displaySchemes(data.eligible_schemes);
        }
        
    } catch (error) {
        showError('Failed to send message. Please try again.');
        console.error('Send message error:', error);
    } finally {
        showLoading(false);
        setInputEnabled(true);
        messageInput.focus();
    }
}

/**
 * Handle language change
 */
async function handleLanguageChange() {
    const newLanguage = languageSelect.value;
    
    if (newLanguage === currentLanguage) {
        return;
    }
    
    currentLanguage = newLanguage;
    
    // Clear current conversation
    messagesContainer.innerHTML = '';
    schemesContainer.style.display = 'none';
    
    // Start new conversation in selected language
    await startConversation();
}

/**
 * Add a message to the chat
 */
function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Display eligible schemes
 */
function displaySchemes(schemes) {
    schemesList.innerHTML = '';
    
    schemes.forEach(scheme => {
        const schemeCard = document.createElement('div');
        schemeCard.className = 'scheme-card';
        
        const schemeName = currentLanguage === 'hi' ? scheme.name_hi : scheme.name;
        
        schemeCard.innerHTML = `
            <h3>${schemeName}</h3>
            <span class="category">${formatCategory(scheme.category)}</span>
            <p class="explanation">${scheme.explanation}</p>
            <p class="confidence">Confidence: ${(scheme.confidence * 100).toFixed(0)}%</p>
        `;
        
        schemesList.appendChild(schemeCard);
    });
    
    schemesContainer.style.display = 'block';
    
    // Scroll schemes into view
    setTimeout(() => {
        schemesContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
}

/**
 * Format category name
 */
function formatCategory(category) {
    const categoryMap = {
        'education': '📚 Education',
        'housing': '🏠 Housing',
        'agriculture': '🌾 Agriculture',
        'entrepreneurship': '💼 Business',
        'pension': '👴 Pension',
        'social_welfare': '🤝 Social Welfare',
        'general': '📋 General'
    };
    
    return categoryMap[category] || category;
}

/**
 * Show/hide loading indicator
 */
function showLoading(show) {
    loadingIndicator.style.display = show ? 'flex' : 'none';
}

/**
 * Enable/disable input
 */
function setInputEnabled(enabled) {
    messageInput.disabled = !enabled;
    sendButton.disabled = !enabled;
}

/**
 * Show error message
 */
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    messagesContainer.appendChild(errorDiv);
    
    // Remove after 5 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
    
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Cleanup on page unload
 */
window.addEventListener('beforeunload', async () => {
    if (sessionId) {
        // End conversation (fire and forget)
        fetch(`${API_BASE_URL}/conversation/${sessionId}`, {
            method: 'DELETE',
            keepalive: true
        }).catch(() => {
            // Ignore errors on cleanup
        });
    }
});
