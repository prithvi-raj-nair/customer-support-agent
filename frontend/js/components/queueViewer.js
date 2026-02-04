// Queue viewer component
async function initQueueViewer() {
    await loadQueue();

    document.getElementById('refresh-queue-btn').addEventListener('click', loadQueue);
}

async function loadQueue() {
    try {
        const data = await api.getQueue();
        const container = document.getElementById('queue-container');

        if (!data.queue || data.queue.length === 0) {
            container.innerHTML = '<p class="placeholder">No items in queue.</p>';
            return;
        }

        let html = '';
        data.queue.forEach(item => {
            const resolvedClass = item.resolved ? 'resolved' : '';
            html += `
                <div class="queue-item ${resolvedClass}" data-id="${item.id}">
                    <h3>
                        ${item.resolved ? '✅' : '⏳'} From: ${item.email_input.sender_email}
                    </h3>
                    <p class="reason"><strong>Reason:</strong> ${escapeHtml(item.reason)}</p>
                    <div class="email-preview">
                        <p><strong>Subject:</strong> ${escapeHtml(item.email_input.subject)}</p>
                        <p>${escapeHtml(item.email_input.body.substring(0, 200))}${item.email_input.body.length > 200 ? '...' : ''}</p>
                    </div>
                    <p style="font-size: 0.8rem; color: #666;">
                        Added: ${new Date(item.timestamp).toLocaleString()}
                    </p>
                    ${!item.resolved ? `<button onclick="resolveItem('${item.id}')">Mark Resolved</button>` : ''}
                </div>
            `;
        });

        container.innerHTML = html;
    } catch (error) {
        console.error('Failed to load queue:', error);
    }
}

async function resolveItem(itemId) {
    try {
        await api.resolveQueueItem(itemId);
        await loadQueue();
    } catch (error) {
        console.error('Failed to resolve item:', error);
        alert('Failed to resolve item');
    }
}
