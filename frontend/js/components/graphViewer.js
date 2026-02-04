// Graph viewer component using Mermaid
async function initGraphViewer() {
    try {
        const data = await api.getGraphDefinition();
        const graphContainer = document.getElementById('mermaid-graph');

        // Initialize mermaid
        mermaid.initialize({
            startOnLoad: false,
            theme: 'default',
            securityLevel: 'loose'
        });

        // Render the graph
        const { svg } = await mermaid.render('graph-svg', data.mermaid);
        graphContainer.innerHTML = svg;

    } catch (error) {
        console.error('Failed to load graph:', error);
        document.getElementById('mermaid-graph').innerHTML =
            '<p class="placeholder">Failed to load graph. Make sure the backend is running.</p>';
    }
}
