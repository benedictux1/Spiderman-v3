// Browser Console Test Script for Tag Assignment
// Copy and paste this into your browser console while on the contact page

console.log("🔍 Tag Assignment Debug Script");
console.log("================================");

// Check if we're on a contact profile page
const contactIdInput = document.getElementById('selected-contact-id');
const tagSelect = document.getElementById('tag-select');
const assignBtn = document.getElementById('assign-tag-btn');

console.log("1. Elements found:");
console.log("   - Contact ID input:", !!contactIdInput);
console.log("   - Tag select:", !!tagSelect);
console.log("   - Assign button:", !!assignBtn);

if (contactIdInput) {
    console.log("\n2. Contact ID:");
    console.log("   - Value:", contactIdInput.value);
    console.log("   - Type:", typeof contactIdInput.value);
    console.log("   - Empty?:", !contactIdInput.value);
}

if (tagSelect) {
    console.log("\n3. Tag Select:");
    console.log("   - Value:", tagSelect.value);
    console.log("   - Options:", tagSelect.options.length);
    for (let i = 0; i < tagSelect.options.length; i++) {
        console.log(`     ${i}: value="${tagSelect.options[i].value}" text="${tagSelect.options[i].text}"`);
    }
}

// Test assignment function
async function testTagAssignment() {
    console.log("\n4. Testing Tag Assignment:");
    
    if (!contactIdInput || !contactIdInput.value) {
        console.error("   ❌ No contact selected!");
        return;
    }
    
    if (!tagSelect || !tagSelect.value) {
        console.error("   ❌ No tag selected!");
        return;
    }
    
    const contactId = contactIdInput.value;
    const tagId = parseInt(tagSelect.value);
    
    console.log(`   - Contact ID: ${contactId}`);
    console.log(`   - Tag ID: ${tagId} (parsed from "${tagSelect.value}")`);
    
    const url = `/api/contacts/${contactId}/tags`;
    const payload = { tag_id: tagId };
    
    console.log(`   - URL: ${url}`);
    console.log(`   - Payload:`, payload);
    
    try {
        console.log("   - Sending request...");
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(payload)
        });
        
        console.log(`   - Response status: ${response.status} ${response.statusText}`);
        console.log(`   - Response headers:`, Object.fromEntries(response.headers.entries()));
        
        const responseText = await response.text();
        console.log(`   - Response body (raw): "${responseText}"`);
        
        try {
            const responseJson = JSON.parse(responseText);
            console.log(`   - Response JSON:`, responseJson);
            
            if (response.ok) {
                console.log("   ✅ SUCCESS!");
            } else {
                console.error(`   ❌ FAILED: ${responseJson.error || 'Unknown error'}`);
            }
        } catch (e) {
            console.error(`   ❌ Response is not JSON: ${e.message}`);
        }
    } catch (error) {
        console.error(`   ❌ Request failed:`, error);
    }
}

console.log("\n5. To test assignment, run:");
console.log("   testTagAssignment()");
console.log("\nMake sure you:");
console.log("   1. Have a contact loaded (contact ID is set)");
console.log("   2. Have selected a tag from the dropdown");


