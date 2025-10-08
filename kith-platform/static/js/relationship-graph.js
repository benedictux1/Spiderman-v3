/**
 * Relationship Graph Module
 * Handles visualization and management of contact relationships using vis.js
 */

let network = null;
let graphData = { nodes: [], edges: [] };

// === GRAPH INITIALIZATION ===

async function initializeGraphView() {
    console.log('Initializing relationship graph...');
    
    // ==== DIAGNOSTIC LOGGING ====
    console.log('🔍 PRE-INIT DIAGNOSTIC:');
    const graphViewEl = document.getElementById('graph-view');
    const mainViewEl = document.getElementById('main-view');
    const container = document.querySelector('.container');
    
    console.log('  graph-view exists:', !!graphViewEl);
    console.log('  graph-view display:', graphViewEl ? getComputedStyle(graphViewEl).display : 'N/A');
    console.log('  graph-view offsetParent:', graphViewEl ? graphViewEl.offsetParent : 'N/A');
    console.log('  main-view display:', mainViewEl ? getComputedStyle(mainViewEl).display : 'N/A');
    console.log('  container display:', container ? getComputedStyle(container).display : 'N/A');
    
    try {
        // Ensure the graph view is visible before any sizing/initialization
        if (graphViewEl && getComputedStyle(graphViewEl).display === 'none') {
            console.warn('Graph view was hidden at init; forcing visible');
            graphViewEl.style.display = 'block';
        }
        // Briefly defer to allow layout to compute if it was just shown
        await new Promise(r => setTimeout(r, 0));

        // Fetch graph data from API with cache busting
        const response = await fetch(`/api/graph-data?t=${Date.now()}`, { credentials: 'include' });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Graph data received:', data);
        
        // Prepare nodes and edges for vis.js
        const nodes = new vis.DataSet(data.nodes);
        const edges = new vis.DataSet(data.edges);
        
        graphData = { nodes, edges };
        
        // Get container
        const container = document.getElementById('graph-container');
        if (!container) {
            throw new Error('Graph container not found');
        }
        
        // Configure vis.js options
        const options = {
            physics: {
                enabled: true,
                stabilization: { iterations: 100 },
                barnesHut: {
                    gravitationalConstant: -2000,
                    centralGravity: 0.3,
                    springLength: 200,
                    springConstant: 0.04,
                    damping: 0.09
                }
            },
            interaction: {
                dragNodes: true,
                dragView: true,
                zoomView: true
            },
            groups: {},
            nodes: {
                shape: 'dot',
                borderWidth: 2,
                font: { 
                    size: 14, 
                    color: '#333',
                    strokeWidth: 2,
                    strokeColor: 'white'
                },
                scaling: {
                    min: 20,
                    max: 50
                }
            },
            edges: {
                width: 2,
                color: { 
                    color: '#cccccc', 
                    highlight: '#848484' 
                },
                font: { 
                    align: 'top',
                    size: 12,
                    color: '#666'
                },
                smooth: {
                    type: 'continuous',
                    roundness: 0.2
                }
            }
        };
        
        // Populate the vis.js groups object with colors from our API
        for (const groupId in data.groups) {
            options.groups[groupId] = { 
                color: data.groups[groupId].color,
                borderWidth: 2
            };
        }
        
        // Create the network
        network = new vis.Network(container, graphData, options);
        
        // ==== POST-NETWORK-CREATION DIAGNOSTIC ====
        console.log('🔍 POST-NETWORK-CREATION DIAGNOSTIC:');
        console.log('  graph-view display:', getComputedStyle(graphViewEl).display);
        console.log('  graph-view offsetParent:', graphViewEl.offsetParent);
        console.log('  main-view display:', mainViewEl ? getComputedStyle(mainViewEl).display : 'N/A');
        console.log('  graph-container rect:', container.getBoundingClientRect());
        const canvas = container.querySelector('canvas');
        console.log('  canvas exists:', !!canvas);
        console.log('  canvas rect:', canvas ? canvas.getBoundingClientRect() : 'N/A');
        
        // Add event listeners
        network.on('click', function(params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                console.log('🖱️ Node clicked:', nodeId);
            }
        });
        
        // Add double-click event listener for navigation to contact profile
        network.on('doubleClick', function(params) {
            console.log('🖱️🖱️ Double-click event triggered!', params);
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                console.log('🖱️🖱️ Node double-clicked:', nodeId);
                
                // If it's not the "You" node, navigate to contact profile
                if (nodeId !== 0) {
                    console.log('🚀 Navigating to contact profile for node:', nodeId);
                    navigateToContactProfile(nodeId);
                } else {
                    console.log('ℹ️ Ignoring double-click on "You" node');
                }
            } else {
                console.log('ℹ️ Double-click on empty space (no node)');
            }
        });
        
        // Fit the network to show all nodes
        setTimeout(() => {
            network.fit();
        }, 500);

        // Safety: if some other script hides graph view after we show it, bring it back
        setTimeout(() => {
            if (graphViewEl && getComputedStyle(graphViewEl).display === 'none') {
                console.warn('Graph view was hidden post-init; restoring visibility');
                graphViewEl.style.display = 'block';
                try { network.redraw(); network.fit(); } catch (e) { /* no-op */ }
            }
        }, 300);

        // Extra guard: keep graph view visible for a short window if other scripts toggle views
        if (graphViewEl) {
            const endAt = Date.now() + 4000; // 4s guard window
            const visGuard = setInterval(() => {
                if (Date.now() > endAt) { clearInterval(visGuard); return; }
                if (getComputedStyle(graphViewEl).display === 'none') {
                    console.warn('Graph view hidden by another script; re-showing');
                    graphViewEl.style.display = 'block';
                    try { network.redraw(); network.fit(); } catch (e) { /* no-op */ }
                }
            }, 150);
        }
        
        console.log('Graph initialized successfully');
        
        // ==== FINAL DIAGNOSTIC ====
        console.log('🔍 FINAL DIAGNOSTIC (after all timeouts):');
        setTimeout(() => {
            console.log('  graph-view display:', getComputedStyle(graphViewEl).display);
            console.log('  graph-view offsetParent:', graphViewEl.offsetParent);
            console.log('  main-view display:', mainViewEl ? getComputedStyle(mainViewEl).display : 'N/A');
            const finalCanvas = container.querySelector('canvas');
            console.log('  canvas rect:', finalCanvas ? finalCanvas.getBoundingClientRect() : 'N/A');
            
            // Check all parents
            let parent = graphViewEl.parentElement;
            let level = 1;
            while (parent && level <= 5) {
                console.log(`  parent[${level}] (${parent.tagName}${parent.id ? '#' + parent.id : ''}${parent.className ? '.' + parent.className : ''}) display:`, getComputedStyle(parent).display);
                parent = parent.parentElement;
                level++;
            }
        }, 5000);
        
    } catch (error) {
        console.error('Failed to initialize graph:', error);
        window.showToast('Failed to load relationship graph', 'error');
        console.error('Graph fetch error details:', error);
    }
}

// === NAVIGATION CONTROLS ===

function setupNavigationControls() {
    const mainViewBtn = document.getElementById('main-view-btn');
    const graphViewBtn = document.getElementById('graph-view-btn');
    const manageGraphBtn = document.getElementById('manage-graph-btn');
    const settingsBtn = document.getElementById('settings-btn');
    const backToMainBtn = document.getElementById('back-to-main-from-graph');
    
    const mainView = document.getElementById('main-view');
    const graphView = document.getElementById('graph-view');
    const profileView = document.getElementById('profile-view');
    const reviewView = document.getElementById('review-view');
    
    // Show main view
    mainViewBtn.addEventListener('click', () => {
        hideAllViews();
        mainView.style.display = 'block';
        setActiveNavButton('main-view-btn');
    });
    
    // Show graph view
    graphViewBtn.addEventListener('click', () => {
        console.log('🎯 Graph button clicked!');
        console.log('  Before hideAllViews - graph-view display:', getComputedStyle(graphView).display);
        console.log('  Before hideAllViews - main-view display:', getComputedStyle(mainView).display);
        
        hideAllViews();
        
        console.log('  After hideAllViews - graph-view display:', getComputedStyle(graphView).display);
        console.log('  After hideAllViews - main-view display:', getComputedStyle(mainView).display);
        
        graphView.style.display = 'block';
        
        console.log('  After setting block - graph-view display:', getComputedStyle(graphView).display);
        console.log('  After setting block - graph-view offsetParent:', graphView.offsetParent);
        
        setActiveNavButton('graph-view-btn');
        
        // Initialize graph if not already done
        if (!network) {
            console.log('  Network not initialized, calling initializeGraphView()');
            initializeGraphView();
        } else {
            console.log('  Network already exists, calling refreshGraphData()');
            // Refresh the graph data
            refreshGraphData();
        }
    });
    
    // Show manage graph modal
    manageGraphBtn.addEventListener('click', () => {
        showManageGraphModal();
    });
    
    // Show settings view
    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            hideAllViews();
            const settingsView = document.getElementById('settings-view');
            if (settingsView) {
                settingsView.style.display = 'block';
                setActiveNavButton('settings-btn');
                
                // Load tags for management if tag management is available
                if (window.tagManagement && window.tagManagement.loadAllTags) {
                    window.tagManagement.loadAllTags();
                }
                
                // Load contacts for management
                if (typeof loadContacts === 'function') {
                    loadContacts();
                }
            }
        });
    }
    
    // Back to main from graph
    backToMainBtn.addEventListener('click', () => {
        hideAllViews();
        mainView.style.display = 'block';
        setActiveNavButton('main-view-btn');
    });
    
    function hideAllViews() {
        mainView.style.display = 'none';
        graphView.style.display = 'none';
        profileView.style.display = 'none';
        reviewView.style.display = 'none';
        const settingsView = document.getElementById('settings-view');
        if (settingsView) settingsView.style.display = 'none';
    }
    
    function setActiveNavButton(activeId) {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(activeId).classList.add('active');
    }
}

// === GRAPH CONTROLS ===

function setupGraphControls() {
    const fitGraphBtn = document.getElementById('fit-graph-btn');
    const resetPhysicsBtn = document.getElementById('reset-physics-btn');
    const showLabelsCheckbox = document.getElementById('show-labels-checkbox');
    
    if (fitGraphBtn) {
        fitGraphBtn.addEventListener('click', () => {
            if (network) {
                network.fit();
            }
        });
    }
    
    if (resetPhysicsBtn) {
        resetPhysicsBtn.addEventListener('click', () => {
            if (network) {
                network.setOptions({ physics: { enabled: true } });
                setTimeout(() => {
                    network.setOptions({ physics: { enabled: false } });
                }, 3000);
            }
        });
    }
    
    if (showLabelsCheckbox) {
        showLabelsCheckbox.addEventListener('change', (e) => {
            if (network) {
                const showLabels = e.target.checked;
                network.setOptions({
                    nodes: {
                        font: showLabels ? { size: 14 } : { size: 0 }
                    }
                });
            }
        });
    }
}

// === GRAPH MANAGEMENT MODAL ===

async function showManageGraphModal() {
    const modal = document.getElementById('manage-graph-modal');
    const sourceSelect = document.getElementById('rel-source-contact');
    const targetSelect = document.getElementById('rel-target-contact');
    
    try {
        // Populate contact dropdowns
        const response = await fetch('/api/contacts', { credentials: 'include' });
        const contacts = await response.json();
        
        sourceSelect.innerHTML = '<option value="">Select first contact...</option>';
        targetSelect.innerHTML = '<option value="">Select second contact...</option>';
        
        contacts.forEach(contact => {
            const option1 = new Option(contact.full_name, contact.id);
            const option2 = new Option(contact.full_name, contact.id);
            sourceSelect.add(option1);
            targetSelect.add(option2);
        });
        
        modal.style.display = 'flex';
    } catch (error) {
        console.error('Failed to load contacts for relationship management:', error);
        window.showToast('Could not load contacts for relationship management', 'error');
    }
}

function setupGraphManagement() {
    const modal = document.getElementById('manage-graph-modal');
    const createGroupBtn = document.getElementById('create-group-btn');
    const createRelBtn = document.getElementById('create-rel-btn');
    const closeModalBtns = document.querySelectorAll('.close-modal-btn');
    
    // Create group
    createGroupBtn.addEventListener('click', async () => {
        const name = document.getElementById('new-group-name').value.trim();
        const color = document.getElementById('new-group-color').value;
        
        if (!name) {
            window.showToast('Group name is required', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/groups', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ name, color })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to create group');
            }
            
            window.showToast('Group created successfully!', 'success');
            
            // Clear form
            document.getElementById('new-group-name').value = '';
            document.getElementById('new-group-color').value = '#97C2FC';
            
            // Refresh graph
            refreshGraphData();
            
        } catch (error) {
            console.error('Failed to create group:', error);
            window.showToast(error.message, 'error');
        }
    });
    
    // Create relationship
    createRelBtn.addEventListener('click', async () => {
        const sourceId = document.getElementById('rel-source-contact').value;
        const targetId = document.getElementById('rel-target-contact').value;
        const label = document.getElementById('rel-label').value.trim();
        
        if (!sourceId || !targetId) {
            window.showToast('Both contacts must be selected', 'error');
            return;
        }
        
        if (sourceId === targetId) {
            window.showToast('A contact cannot have a relationship with themselves', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/relationships', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ 
                    source_contact_id: parseInt(sourceId), 
                    target_contact_id: parseInt(targetId), 
                    label: label || 'Connected'
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to create relationship');
            }
            
            window.showToast('Relationship created successfully!', 'success');
            
            // Clear form
            document.getElementById('rel-source-contact').value = '';
            document.getElementById('rel-target-contact').value = '';
            document.getElementById('rel-label').value = '';
            
            // Refresh graph
            refreshGraphData();
            
        } catch (error) {
            console.error('Failed to create relationship:', error);
            window.showToast(error.message, 'error');
        }
    });
    
    // Close modal
    closeModalBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    });
    
    // Close modal when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// === UTILITY FUNCTIONS ===

async function refreshGraphData() {
    if (!network) return;
    
    try {
        const response = await fetch(`/api/graph-data?t=${Date.now()}`, { credentials: 'include' });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update the network data
        graphData.nodes.clear();
        graphData.edges.clear();
        graphData.nodes.add(data.nodes);
        graphData.edges.add(data.edges);
        
        // Update group colors
        const options = network.getOptionsFromConfigurator();
        options.groups = {};
        for (const groupId in data.groups) {
            options.groups[groupId] = { 
                color: data.groups[groupId].color,
                borderWidth: 2
            };
        }
        network.setOptions(options);
        
        console.log('Graph data refreshed');
        
    } catch (error) {
        console.error('Failed to refresh graph data:', error);
        window.showToast('Failed to refresh graph', 'error');
    }
}

function showContactProfile(contactId) {
    // This function should integrate with the existing contact profile functionality
    // For now, we'll just log the contact ID
    console.log('Show contact profile for ID:', contactId);
    
    // You can integrate this with the existing profile view logic
    // by calling the appropriate function from main.js or contacts.js
    if (typeof window.showContactProfile === 'function') {
        window.showContactProfile(contactId);
    }
}

function navigateToContactProfile(contactId) {
    console.log('📍 navigateToContactProfile called with ID:', contactId);
    
    // Get the contact name from the graph data
    const contactNode = graphData.nodes.get(contactId);
    const contactName = contactNode ? contactNode.label : 'Contact';
    console.log('📍 Contact name:', contactName);
    
    // Use the existing openContactProfile function from main.js
    console.log('📍 Checking for window.openContactProfile:', typeof window.openContactProfile);
    if (typeof window.openContactProfile === 'function') {
        console.log('✅ Calling window.openContactProfile');
        window.openContactProfile(contactId, contactName);
    } else if (typeof window.viewContactProfile === 'function') {
        console.log('✅ Calling window.viewContactProfile');
        window.viewContactProfile(contactId);
    } else {
        // Fallback: try to navigate manually
        console.log('⚠️ Fallback navigation to contact profile');
        
        // Hide graph view and show profile view
        const graphView = document.getElementById('graph-view');
        const profileView = document.getElementById('profile-view');
        const mainView = document.getElementById('main-view');
        
        console.log('📍 graphView exists:', !!graphView);
        console.log('📍 profileView exists:', !!profileView);
        console.log('📍 mainView exists:', !!mainView);
        
        if (graphView) graphView.style.display = 'none';
        if (mainView) mainView.style.display = 'none';
        if (profileView) profileView.style.display = 'block';
        
        // Set the contact ID
        const hiddenId = document.getElementById('selected-contact-id');
        if (hiddenId) {
            hiddenId.value = String(contactId);
            console.log('✅ Set selected-contact-id to:', contactId);
        }
        
        // Update the header
        const header = document.getElementById('contact-profile-name');
        if (header) {
            header.textContent = contactName;
            console.log('✅ Set contact-profile-name to:', contactName);
        }
        
        // Load the contact profile
        console.log('📍 Checking for window.loadContactProfile:', typeof window.loadContactProfile);
        if (typeof window.loadContactProfile === 'function') {
            console.log('✅ Calling window.loadContactProfile');
            window.loadContactProfile(contactId);
        }
    }
}

// Use window.showToast directly - it's defined in ui-enhancements.js

// === INITIALIZATION ===

document.addEventListener('DOMContentLoaded', function() {
    console.log('Relationship graph module loaded');
    
    // Setup all event listeners
    setupNavigationControls();
    setupGraphControls();
    setupGraphManagement();
    
    console.log('Relationship graph controls initialized');
});
