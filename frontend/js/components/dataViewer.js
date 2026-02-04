// Data viewer component
async function initDataViewer() {
    await loadUsers();
    await loadOrders();
    await loadSentEmails();

    // Set up user filter
    const userFilter = document.getElementById('user-filter');
    userFilter.addEventListener('change', async (e) => {
        await loadOrders(e.target.value);
    });

    // Set up refresh button
    document.getElementById('refresh-emails-btn').addEventListener('click', loadSentEmails);
}

async function loadUsers() {
    try {
        const data = await api.getUsers();
        const tbody = document.querySelector('#users-table tbody');
        const userFilter = document.getElementById('user-filter');

        // Clear existing options except "All Users"
        while (userFilter.options.length > 1) {
            userFilter.remove(1);
        }

        let html = '';
        data.users.forEach(user => {
            html += `
                <tr>
                    <td>${user.user_id}</td>
                    <td>${user.name}</td>
                    <td>${user.email}</td>
                </tr>
            `;

            // Add to filter dropdown
            const option = document.createElement('option');
            option.value = user.user_id;
            option.textContent = `${user.name} (${user.email})`;
            userFilter.appendChild(option);
        });

        tbody.innerHTML = html || '<tr><td colspan="3">No users found</td></tr>';
    } catch (error) {
        console.error('Failed to load users:', error);
    }
}

async function loadOrders(userId = null) {
    try {
        const data = await api.getOrders(userId);
        const tbody = document.querySelector('#orders-table tbody');

        let html = '';
        data.orders.forEach(order => {
            html += `
                <tr>
                    <td>${order.order_id}</td>
                    <td>${order.user_id}</td>
                    <td>${order.product_name}</td>
                    <td><span class="status-badge ${order.status}">${formatStatus(order.status)}</span></td>
                    <td>${order.estimated_delivery || '-'}</td>
                    <td>$${order.total_amount.toFixed(2)}</td>
                </tr>
            `;
        });

        tbody.innerHTML = html || '<tr><td colspan="6">No orders found</td></tr>';
    } catch (error) {
        console.error('Failed to load orders:', error);
    }
}

async function loadSentEmails() {
    try {
        const data = await api.getSentEmails();
        const container = document.getElementById('sent-emails-container');

        if (!data.emails || data.emails.length === 0) {
            container.innerHTML = '<p class="placeholder">No emails sent yet.</p>';
            return;
        }

        let html = '';
        // Show most recent first
        [...data.emails].reverse().forEach(email => {
            html += `
                <div class="sent-email">
                    <p><strong>To:</strong> ${email.to_email}</p>
                    <p><strong>Subject:</strong> ${email.subject}</p>
                    <p class="timestamp">${new Date(email.timestamp).toLocaleString()}</p>
                    <p style="margin-top: 0.5rem; white-space: pre-wrap;">${escapeHtml(email.body)}</p>
                </div>
            `;
        });

        container.innerHTML = html;
    } catch (error) {
        console.error('Failed to load sent emails:', error);
    }
}

function formatStatus(status) {
    return status
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}
