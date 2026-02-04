// Trace viewer component
function displayTrace(trace) {
    const container = document.getElementById('trace-container');

    if (!trace || trace.length === 0) {
        container.innerHTML = '<div class="placeholder">No trace data available.</div>';
        return;
    }

    let html = '';

    trace.forEach((step, index) => {
        const duration = step.duration_ms ? `${step.duration_ms.toFixed(0)}ms` : '-';
        const timestamp = new Date(step.timestamp).toLocaleTimeString();

        html += `
            <div class="trace-step">
                <span class="node-name">${index + 1}. ${formatNodeName(step.node)}</span>
                <span class="duration">${duration}</span>
                <div class="details">
                    <p><strong>Time:</strong> ${timestamp}</p>
                    ${step.input_summary ? `<p><strong>Input:</strong> ${escapeHtml(step.input_summary)}</p>` : ''}
                    ${step.output_summary ? `<p><strong>Output:</strong> ${escapeHtml(step.output_summary)}</p>` : ''}
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function formatNodeName(name) {
    return name
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}
