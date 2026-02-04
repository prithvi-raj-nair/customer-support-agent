// Response viewer component
function displayResponse(result) {
    const container = document.getElementById('response-container');

    if (!result.success && !result.response_email) {
        container.innerHTML = `
            <div class="response-email" style="border-color: #dc3545;">
                <div class="email-header">
                    <p><strong>Error:</strong> ${result.error || 'Unknown error occurred'}</p>
                </div>
            </div>
        `;
        return;
    }

    let badgeClass = 'default';
    let badgeText = result.routed_to;

    if (result.routed_to === 'automated_response') {
        badgeClass = 'automated';
        badgeText = 'Automated Response';
    } else if (result.routed_to === 'human_queue') {
        badgeClass = 'human';
        badgeText = 'Routed to Human';
    } else if (result.routed_to === 'default_response') {
        badgeClass = 'default';
        badgeText = 'Default Response';
    }

    const email = result.response_email;

    let html = `
        <div class="response-email">
            <div class="email-header">
                <p>
                    <strong>Status:</strong>
                    <span class="routed-badge ${badgeClass}">${badgeText}</span>
                </p>
    `;

    if (email) {
        html += `
                <p><strong>To:</strong> ${email.to_email}</p>
                <p><strong>Subject:</strong> ${email.subject}</p>
                <p><strong>Timestamp:</strong> ${new Date(email.timestamp).toLocaleString()}</p>
            </div>
            <div class="email-body">${escapeHtml(email.body)}</div>
        `;
    } else {
        html += `
            </div>
            <div class="email-body">
                <em>No email response generated.</em>
                ${result.escalation_reason ? `<br><br><strong>Reason:</strong> ${escapeHtml(result.escalation_reason)}` : ''}
            </div>
        `;
    }

    html += '</div>';
    container.innerHTML = html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
