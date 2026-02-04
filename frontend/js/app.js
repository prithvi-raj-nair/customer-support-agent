// Main app initialization
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize tab navigation
    initTabs();

    // Initialize components
    initEmailForm();

    // Load graph when tab is first shown
    let graphLoaded = false;
    let dataLoaded = false;
    let queueLoaded = false;

    // Tab change handler
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const tab = btn.dataset.tab;

            if (tab === 'graph' && !graphLoaded) {
                await initGraphViewer();
                graphLoaded = true;
            } else if (tab === 'data' && !dataLoaded) {
                await initDataViewer();
                dataLoaded = true;
            } else if (tab === 'queue' && !queueLoaded) {
                await initQueueViewer();
                queueLoaded = true;
            }
        });
    });
});

function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons and contents
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            // Add active class to clicked button
            btn.classList.add('active');

            // Show corresponding content
            const tabId = btn.dataset.tab + '-tab';
            document.getElementById(tabId).classList.add('active');
        });
    });
}
