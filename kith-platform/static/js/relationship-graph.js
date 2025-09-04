/**
 * Relationship Graph Module
 * Handles visualization and management of contact relationships using vis.js
 */

let network = null;
let graphData = { nodes: [], edges: [] };

// === GRAPH INITIALIZATION ===

async function initializeGraphView() {
    console.log('Initializing relationship graph...');
    
    try {
        // Fetch graph data from API with cache busting
        const response = await fetch(`/api/graph-data?t=${Date.now()}`);
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
        
        // Add event listeners
        network.on('click', function(params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                console.log('Node clicked:', nodeId);
                
                // If it's not the "You" node, show contact profile
                if (nodeId !== 0) {
                    showContactProfile(nodeId);
                }
            }
        });
        
        // Fit the network to show all nodes
        setTimeout(() => {
            network.fit();
        }, 500);
        
        console.log('Graph initialized successfully');
        
    } catch (error) {
        console.error('Failed to initialize graph:', error);
        window.showToast('Failed to load relationship graph', 'error');
    }
}

// === NAVIGATION CONTROLS ===

function setupNavigationControls() {
    const mainViewBtn = document.getElementById('main-view-btn');
    const graphViewBtn = document.getElementById('graph-view-btn');
    const manageGraphBtn = document.getElementById('manage-graph-btn');
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
        hideAllViews();
        graphView.style.display = 'block';
        setActiveNavButton('graph-view-btn');
        
        // Initialize graph if not already done
        if (!network) {
            initializeGraphView();
        } else {
            // Refresh the graph data
            refreshGraphData();
        }
    });
    
    // Show manage graph modal
    manageGraphBtn.addEventListener('click', () => {
        showManageGraphModal();
    });
    
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
        const response = await fetch('/api/contacts');
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
        const response = await fetch(`/api/graph-data?t=${Date.now()}`);
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
