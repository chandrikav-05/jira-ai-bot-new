/**
 * Jira AI Bot - Frontend Logic
 * Handles state management, API calls, and UI updates
 */

const chatWindow = document.getElementById('chat-window');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const fileInput = document.getElementById('file-input');
const uploadTrigger = document.getElementById('upload-trigger');
const actionButtons = document.getElementById('action-buttons');

let currentState = 'IDLE'; // IDLE, GENERATING, PREVIEWING, UPLOADING, SELECTING
let currentTicket = null;
let documentTickets = [];

// ── UI Helpers ──────────────────────────────────────────────────────────────

function addMessage(text, sender = 'bot') {
    const msg = document.createElement('div');
    msg.className = `message ${sender}`;
    msg.textContent = text;
    chatWindow.appendChild(msg);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return msg;
}

function showLoader() {
    const loader = document.createElement('div');
    loader.className = 'message bot loading';
    loader.innerHTML = '<div class="loader"></div>';
    chatWindow.appendChild(loader);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return loader;
}

function renderTicketPreview(ticket, isUpdate = false) {
    const template = document.getElementById('ticket-template');
    const clone = template.content.cloneNode(true);
    const container = clone.querySelector('.ticket-preview');

    container.querySelector('.ticket-summary').textContent = ticket.summary;
    container.querySelector('.ticket-desc').textContent = ticket.description;
    container.querySelector('.priority-val').textContent = ticket.priority;
    container.querySelector('.assignee-val').textContent = ticket.assignee_email || 'Unassigned';
    container.querySelector('.date-val').textContent = ticket.due_date || 'None';
    container.querySelector('.project-val').textContent = ticket.project_key;

    const badge = container.querySelector('.ticket-badge');
    badge.textContent = (ticket.issue_type || 'Task').toUpperCase();
    badge.className = `ticket-badge badge-${(ticket.issue_type || 'task').toLowerCase()}`;

    if (isUpdate) {
        // Find last preview and replace or append
        const lastPreview = chatWindow.querySelector('.ticket-preview:last-child');
        if (lastPreview) {
            lastPreview.replaceWith(container);
        } else {
            chatWindow.appendChild(container);
        }
    } else {
        chatWindow.appendChild(container);
    }
    
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function setActionButtons(buttons) {
    actionButtons.innerHTML = '';
    buttons.forEach(btn => {
        const b = document.createElement('button');
        b.className = 'btn-secondary';
        b.textContent = btn.label;
        b.onclick = btn.action;
        actionButtons.appendChild(b);
    });
    actionButtons.style.display = buttons.length ? 'flex' : 'none';
}

// ── API Calls ───────────────────────────────────────────────────────────────

async function apiPost(endpoint, data) {
    const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const error = await response.json();
        let message = 'API request failed';
        
        if (typeof error.detail === 'string') {
            message = error.detail;
        } else if (Array.isArray(error.detail)) {
            // Handle FastAPI validation errors (list of objects)
            message = error.detail.map(d => `${d.loc.join('.')}: ${d.msg}`).join('; ');
        } else if (typeof error.detail === 'object' && error.detail !== null) {
            message = JSON.stringify(error.detail);
        }
        
        throw new Error(message);
    }
    return response.json();
}

async function handleSend() {
    const text = userInput.value.trim();
    if (!text || currentState === 'GENERATING') return;

    addMessage(text, 'user');
    userInput.value = '';
    const loader = showLoader();

    try {
        if (currentState === 'IDLE' || currentState === 'RESET') {
            // Step 1: Generate initial ticket
            currentState = 'GENERATING';
            const res = await apiPost('/generate-ticket', { user_text: text });
            loader.remove();
            
            currentTicket = res.ticket;
            addMessage("I've generated a draft for you. Does this look correct, or would you like to make changes?");
            renderTicketPreview(currentTicket);
            
            currentState = 'PREVIEWING';
            setActionButtons([
                { label: '🚀 Create in Jira', action: finalizeTicket },
                { label: '🔄 Start Over', action: resetApp }
            ]);
            userInput.placeholder = "Tell me what to change (e.g., 'Make it high priority')...";

        } else if (currentState === 'PREVIEWING') {
            // Step 2: Update existing ticket with feedback
            const res = await apiPost('/update-preview', { 
                current_ticket: currentTicket, 
                feedback: text 
            });
            loader.remove();
            
            currentTicket = res.ticket;
            addMessage("Updated! How about now?");
            renderTicketPreview(currentTicket, true);
        }
    } catch (err) {
        loader.remove();
        addMessage(`Error: ${err.message}`, 'bot');
    }
}

async function finalizeTicket() {
    if (!currentTicket) return;
    const loader = showLoader();
    setActionButtons([]);

    try {
        const res = await apiPost('/create-ticket', { ticket: currentTicket });
        loader.remove();
        
        addMessage(`✅ Success! Ticket created: ${res.result.ticket_id}`, 'bot');
        
        const linkContainer = document.createElement('div');
        linkContainer.className = 'message bot success-link';
        linkContainer.style.marginTop = '-10px';
        linkContainer.innerHTML = `
            <div style="background: rgba(0, 255, 128, 0.1); border: 1px solid var(--primary); padding: 12px; border-radius: 8px; display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.2rem;">🔗</span>
                <a href="${res.result.ticket_url}" target="_blank" style="color: var(--primary); font-weight: 600; text-decoration: none;">View Issue in Jira</a>
            </div>
        `;
        chatWindow.appendChild(linkContainer);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        
        currentState = 'IDLE';
        userInput.placeholder = "Build another ticket...";
    } catch (err) {
        loader.remove();
        addMessage(`Failed to create ticket: ${err.message}`, 'bot');
        setActionButtons([
            { label: 'Retry Creation', action: finalizeTicket },
            { label: 'Cancel', action: resetApp }
        ]);
    }
}

async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    addMessage(`Uploading ${file.name}...`, 'user');
    const loader = showLoader();

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('http://localhost:8000/upload-document', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error("Upload failed");
        
        const res = await response.json();
        loader.remove();
        
        documentTickets = res.tickets;
        addMessage(`Found ${res.count} tasks in the document. Please select which ones you want to create in Jira:`);
        
        renderDocumentTicketList(res.tickets);
        currentState = 'SELECTING';
        
        setActionButtons([
            { label: 'Create Selected', action: createSelectedFromDocument },
            { label: 'Cancel', action: resetApp }
        ]);

    } catch (err) {
        loader.remove();
        addMessage(`Error processing document: ${err.message}`, 'bot');
    }
}

function renderDocumentTicketList(tickets) {
    const grid = document.createElement('div');
    grid.className = 'document-grid';
    
    tickets.forEach((t, i) => {
        const item = document.createElement('div');
        item.className = 'document-item selected'; // Default selected
        item.dataset.index = i;
        item.innerHTML = `
            <div class="checkbox"></div>
            <div style="font-weight:600; margin-bottom:4px;">${t.summary}</div>
            <div style="font-size:0.8rem; color:var(--text-dim);">${t.issue_type} | ${t.priority}</div>
        `;
        item.onclick = () => item.classList.toggle('selected');
        grid.appendChild(item);
    });
    
    chatWindow.appendChild(grid);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function createSelectedFromDocument() {
    const selectedIndices = Array.from(document.querySelectorAll('.document-item.selected'))
        .map(el => parseInt(el.dataset.index));
    
    if (selectedIndices.length === 0) {
        addMessage("Please select at least one ticket.", 'bot');
        return;
    }

    const ticketsToCreate = selectedIndices.map(i => documentTickets[i]);
    const loader = showLoader();
    setActionButtons([]);

    try {
        const res = await apiPost('/create-selected-tickets', { tickets: ticketsToCreate });
        loader.remove();
        addMessage(`✅ Processed ${res.results.length} tickets. Created: ${res.created}, Failed: ${res.failed}.`, 'bot');
        resetApp();
    } catch (err) {
        loader.remove();
        addMessage(`Error creating tickets: ${err.message}`, 'bot');
    }
}

function resetApp() {
    currentState = 'IDLE';
    currentTicket = null;
    documentTickets = [];
    setActionButtons([]);
    userInput.placeholder = "e.g., Fix the login timeout bug...";
    addMessage("App reset. Ready for next task!");
}

// ── Event Listeners ─────────────────────────────────────────────────────────

sendBtn.onclick = handleSend;
userInput.onkeypress = (e) => { if (e.key === 'Enter') handleSend(); };
uploadTrigger.onclick = () => fileInput.click();
fileInput.onchange = handleFileUpload;
