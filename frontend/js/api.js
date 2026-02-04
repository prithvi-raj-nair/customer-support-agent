// API client for the backend
const API_BASE_URL = 'http://localhost:8000/api';

const api = {
    // Process email through the agent
    async processEmail(senderEmail, subject, body) {
        const response = await fetch(`${API_BASE_URL}/email/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sender_email: senderEmail,
                subject: subject,
                body: body
            })
        });
        return response.json();
    },

    // Get sent emails
    async getSentEmails() {
        const response = await fetch(`${API_BASE_URL}/email/sent`);
        return response.json();
    },

    // Get all users
    async getUsers() {
        const response = await fetch(`${API_BASE_URL}/data/users`);
        return response.json();
    },

    // Get orders
    async getOrders(userId = null, days = 14) {
        let url = `${API_BASE_URL}/data/orders?days=${days}`;
        if (userId) {
            url += `&user_id=${userId}`;
        }
        const response = await fetch(url);
        return response.json();
    },

    // Get human queue
    async getQueue() {
        const response = await fetch(`${API_BASE_URL}/queue`);
        return response.json();
    },

    // Resolve queue item
    async resolveQueueItem(itemId) {
        const response = await fetch(`${API_BASE_URL}/queue/${itemId}/resolve`, {
            method: 'POST'
        });
        return response.json();
    },

    // Get graph definition
    async getGraphDefinition() {
        const response = await fetch(`${API_BASE_URL}/graph/definition`);
        return response.json();
    }
};
