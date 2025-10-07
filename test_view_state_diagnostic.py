#!/usr/bin/env python3
"""
Diagnostic test to inject visibility tracking into the browser
Run this after clicking "Relationship Graph" to see what's hiding the view
"""

diagnostic_js = """
// Inject this into the browser console to track view changes
(function() {
    console.log('🔍 VIEW STATE DIAGNOSTIC ACTIVE');
    
    const mainView = document.getElementById('main-view');
    const graphView = document.getElementById('graph-view');
    
    // Store original style setters
    const originalMainStyle = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'style');
    
    // Track all style changes to both views
    function trackStyleChange(element, property, value) {
        const stack = new Error().stack;
        console.log(`🎯 Style change on ${element.id}.style.${property} = ${value}`);
        console.log('📍 Called from:', stack.split('\\n')[3]); // Show caller
        
        // Show current state of both views
        console.log('📊 Current states:');
        console.log('  main-view display:', getComputedStyle(mainView).display);
        console.log('  graph-view display:', getComputedStyle(graphView).display);
    }
    
    // Intercept style.display changes
    ['main-view', 'graph-view'].forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        
        // Create a proxy for the style object
        const originalStyle = el.style;
        const styleProxy = new Proxy(originalStyle, {
            set(target, property, value) {
                if (property === 'display') {
                    trackStyleChange(el, property, value);
                }
                return Reflect.set(target, property, value);
            }
        });
        
        // Replace the style property (this won't work in all browsers, but try anyway)
        try {
            Object.defineProperty(el, 'style', {
                get() { return styleProxy; },
                set(val) { /* ignore */ }
            });
        } catch(e) {
            console.warn('Could not proxy style for', id, e);
        }
    });
    
    // Also log function calls that might hide/show views
    const originalFunctions = {};
    ['showMainView', 'showReviewView', 'showProfileView', 'showSettingsView'].forEach(fnName => {
        if (typeof window[fnName] === 'function') {
            originalFunctions[fnName] = window[fnName];
            window[fnName] = function() {
                console.log(`🎯 ${fnName}() called`);
                console.trace();
                return originalFunctions[fnName].apply(this, arguments);
            };
        }
    });
    
    console.log('✅ Diagnostic ready. Click "Relationship Graph" now.');
    
    // Also check current state
    setTimeout(() => {
        console.log('\\n📊 INITIAL STATE CHECK:');
        console.log('  main-view display:', getComputedStyle(mainView).display);
        console.log('  main-view visible:', mainView.offsetParent !== null);
        console.log('  graph-view display:', getComputedStyle(graphView).display);
        console.log('  graph-view visible:', graphView.offsetParent !== null);
        console.log('  graph-view z-index:', getComputedStyle(graphView).zIndex);
        console.log('  main-view z-index:', getComputedStyle(mainView).zIndex);
    }, 1000);
})();
"""

print("=" * 80)
print("VIEW STATE DIAGNOSTIC SCRIPT")
print("=" * 80)
print("\n1. Open the browser console")
print("2. Copy and paste the following script:")
print("\n" + "─" * 80)
print(diagnostic_js)
print("─" * 80)
print("\n3. Press Enter to execute it")
print("4. Click 'Relationship Graph' button")
print("5. Observe the console output to see what's changing the view states")
print("\n" + "=" * 80)

