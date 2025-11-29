class HistoryChatBot {
    constructor() {
        this.baseURL = "http://localhost:8000";
        this.sessionId = this.generateSessionId();
        this.currentRequest = null;
        
        this.initializeEventListeners();
        this.updateSessionDisplay();
        this.checkHealth();
        this.updateCurrentTime();
        
        // Update time every minute
        setInterval(() => this.updateCurrentTime(), 60000);
    }

    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9);
    }

    initializeEventListeners() {
        const input = document.getElementById('questionInput');
        const sendBtn = document.getElementById('sendButton');
        const charCount = document.getElementById('charCount');

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        input.addEventListener('input', () => {
            const count = input.value.length;
            charCount.textContent = `${count}/500`;
            
            if (count > 450) {
                charCount.style.color = '#dc3545';
            } else if (count > 400) {
                charCount.style.color = '#ffc107';
            } else {
                charCount.style.color = '#6c757d';
            }
        });

        sendBtn.addEventListener('click', () => this.sendMessage());
    }

    updateCurrentTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit'
        });
        document.getElementById('currentTime').textContent = timeString;
    }

    async checkHealth() {
        try {
            const response = await fetch(`${this.baseURL}/health`);
            const data = await response.json();
            
            const statusDot = document.querySelector('.status-dot');
            const statusText = document.querySelector('#status span:last-child');
            
            if (data.kaggle === 'healthy') {
                statusDot.style.background = '#4CAF50';
                statusText.textContent = 'Kết nối thành công';
            } else {
                statusDot.style.background = '#ff9800';
                statusText.textContent = 'Kaggle server không khả dụng';
            }
        } catch (error) {
            console.error('Health check failed:', error);
            const statusDot = document.querySelector('.status-dot');
            const statusText = document.querySelector('#status span:last-child');
            statusDot.style.background = '#f44336';
            statusText.textContent = 'Mất kết nối backend';
        }
    }

    async sendMessage() {
        const input = document.getElementById('questionInput');
        const question = input.value.trim();
        
        if (!question) {
            this.showError('Vui lòng nhập câu hỏi!');
            return;
        }

        if (this.currentRequest) {
            this.currentRequest.abort();
        }

        this.addMessage(question, 'user');
        input.value = '';
        document.getElementById('charCount').textContent = '0/500';

        // Show loading message
        const loadingId = this.addMessage('Đang xử lý...', 'bot', true);

        try {
            this.currentRequest = new AbortController();
            const signal = this.currentRequest.signal;

            const response = await fetch(`${this.baseURL}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    session_id: this.sessionId
                }),
                signal: signal
            });

            if (!response.ok) {
                throw new Error(await response.text());
            }

            const data = await response.json();
            
            // Remove loading message and add actual response
            this.removeMessage(loadingId);
            this.addMessage(data.answer, 'bot');
            
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Request aborted');
                return;
            }
            
            this.removeMessage(loadingId);
            this.addMessage(`Lỗi: ${error.message}`, 'bot');
            console.error('Chat error:', error);
        } finally {
            this.currentRequest = null;
        }
    }

    addMessage(content, sender, isTemp = false) {
        const chatMessages = document.getElementById('chatMessages');
        const messageId = isTemp ? 'temp-' + Date.now() : null;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        if (messageId) {
            messageDiv.id = messageId;
        }
        
        const now = new Date();
        const timeString = now.toLocaleTimeString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        messageDiv.innerHTML = `
            <div class="message-content">${this.formatMessage(content)}</div>
            <div class="message-time">${timeString}</div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageId;
    }

    removeMessage(messageId) {
        const message = document.getElementById(messageId);
        if (message) {
            message.remove();
        }
    }

    formatMessage(content) {
        // Basic formatting - you can enhance this
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }

    updateSessionDisplay() {
        document.getElementById('sessionId').textContent = this.sessionId;
    }

    newSession() {
        this.sessionId = this.generateSessionId();
        this.updateSessionDisplay();
        
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = `
            <div class="message bot-message">
                <div class="message-content">
                    Phiên mới đã bắt đầu! Tôi là trợ lý AI chuyên về lịch sử Việt Nam. 
                    Hãy hỏi tôi bất kỳ câu hỏi nào về lịch sử Việt Nam!
                </div>
                <div class="message-time" id="currentTime"></div>
            </div>
        `;
        this.updateCurrentTime();
        
        this.showSuccess('Đã bắt đầu phiên mới!');
    }

    showError(message) {
        alert(message); // You can replace with a better notification system
    }

    showSuccess(message) {
        console.log(message); // You can replace with a better notification system
    }
}

// Global functions for HTML onclick
function sendMessage() {
    if (window.chatBot) {
        window.chatBot.sendMessage();
    }
}

function newSession() {
    if (window.chatBot) {
        window.chatBot.newSession();
    }
}

function setExample(question) {
    document.getElementById('questionInput').value = question;
    document.getElementById('questionInput').focus();
}

// Initialize chatbot when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.chatBot = new HistoryChatBot();
});