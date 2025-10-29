// Chat Application JavaScript
const API_URL = 'http://localhost:5000';
let socket = null;
let currentRoom = null;
let currentUser = null;
let typingTimeout = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
});

// Check if user is authenticated
function checkAuth() {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    // Get user info
    fetchUserInfo(token);
    
    // Connect to Socket.IO
    connectSocket(token);
    
    // Load rooms
    loadRooms();
}

// Fetch current user info
async function fetchUserInfo(token) {
    try {
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            currentUser = data;
            document.getElementById('userName').textContent = `${data.first_name} ${data.last_name}`;
            document.getElementById('userEmail').textContent = data.email;
        } else {
            // Token invalid, redirect to login
            logout();
        }
    } catch (error) {
        console.error('Error fetching user info:', error);
        showNotification('Failed to load user information', 'error');
    }
}

// Connect to Socket.IO server
function connectSocket(token) {
    socket = io(API_URL, {
        query: { token: token }
    });

    // Connection events
    socket.on('connect', () => {
        console.log('Connected to server:', socket.id);
        updateConnectionStatus(true);
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        updateConnectionStatus(false);
    });

    socket.on('connected', (data) => {
        console.log('Server confirmation:', data);
    });

    // Room events
    socket.on('joined_room', (data) => {
        console.log('Joined room:', data);
        showNotification(`Joined ${data.room_name}`, 'success');
    });

    socket.on('user_joined', (data) => {
        console.log('User joined:', data);
        addSystemMessage(`User ${data.user_id} joined the room`);
    });

    socket.on('user_left', (data) => {
        console.log('User left:', data);
        addSystemMessage(`User ${data.user_id} left the room`);
    });

    socket.on('left_room', (data) => {
        console.log('Left room:', data);
    });

    // Message events
    socket.on('new_message', (message) => {
        console.log('New message:', message);
        displayMessage(message);
    });

    socket.on('messages_history', (data) => {
        console.log('Message history received:', data.messages.length);
        displayMessageHistory(data.messages);
    });

    // Typing events
    socket.on('user_typing', (data) => {
        console.log('User typing:', data);
        showTypingIndicator(data.is_typing);
    });

    // Error handling
    socket.on('error', (data) => {
        console.error('Socket error:', data);
        showNotification(data.message || 'An error occurred', 'error');
    });
}

// Update connection status indicator
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connectionStatus');
    if (connected) {
        statusEl.innerHTML = '● Connected';
        statusEl.className = 'chat-status status-online';
    } else {
        statusEl.innerHTML = '● Disconnected';
        statusEl.className = 'chat-status';
        statusEl.style.color = '#f44336';
    }
}

// Load all rooms
async function loadRooms() {
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch(`${API_URL}/chat/rooms`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            displayRooms(data.rooms);
        } else {
            console.error('Failed to load rooms');
            showNotification('Failed to load rooms', 'error');
        }
    } catch (error) {
        console.error('Error loading rooms:', error);
        showNotification('Failed to load rooms', 'error');
    }
}

// Display rooms in sidebar
function displayRooms(rooms) {
    const roomsList = document.getElementById('roomsList');
    
    if (rooms.length === 0) {
        roomsList.innerHTML = `
            <div class="empty-rooms">
                <p>No rooms yet</p>
                <button class="create-room-btn" onclick="openCreateRoomModal()">Create First Room</button>
            </div>
        `;
        return;
    }

    roomsList.innerHTML = rooms.map(room => `
        <div class="room-item" data-room-id="${room.id}" onclick="selectRoom(${room.id}, '${room.name.replace(/'/g, "\\'")}')">
            <div class="room-name">${escapeHtml(room.name)}</div>
            <div class="room-creator">Created by ${escapeHtml(room.creator.first_name)} ${escapeHtml(room.creator.last_name)}</div>
        </div>
    `).join('');
}

// Select a room
function selectRoom(roomId, roomName) {
    // Leave current room if any
    if (currentRoom) {
        socket.emit('leave_room', { room_id: currentRoom.id });
    }

    // Update UI
    document.querySelectorAll('.room-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-room-id="${roomId}"]`)?.classList.add('active');

    // Hide welcome screen, show chat
    document.getElementById('welcomeScreen').style.display = 'none';
    const chatArea = document.getElementById('chatArea');
    chatArea.className = 'chat-area-visible';

    // Update current room
    currentRoom = { id: roomId, name: roomName };
    document.getElementById('currentRoomName').textContent = roomName;

    // Clear messages
    document.getElementById('messagesContainer').innerHTML = '';

    // Join room via Socket.IO
    socket.emit('join_room', { room_id: roomId });

    // Load message history
    socket.emit('get_messages', { room_id: roomId, limit: 50 });
}

// Display message history
function displayMessageHistory(messages) {
    const container = document.getElementById('messagesContainer');
    container.innerHTML = '';
    
    messages.forEach(message => {
        displayMessage(message, false);
    });

    // Scroll to bottom
    scrollToBottom();
}

// Display a single message
function displayMessage(message, animate = true) {
    const container = document.getElementById('messagesContainer');
    const isOwn = currentUser && message.user_id === currentUser.id;
    
    const messageEl = document.createElement('div');
    messageEl.className = `message ${isOwn ? 'own' : ''}`;
    if (!animate) messageEl.style.animation = 'none';

    const initials = getInitials(message.user.first_name, message.user.last_name);
    const senderName = `${message.user.first_name} ${message.user.last_name}`;
    const time = formatTime(message.timestamp);

    messageEl.innerHTML = `
        <div class="message-avatar">${initials}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-sender">${escapeHtml(senderName)}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-bubble">
                ${escapeHtml(message.content)}
            </div>
        </div>
    `;

    container.appendChild(messageEl);
    scrollToBottom();
}

// Add system message
function addSystemMessage(text) {
    const container = document.getElementById('messagesContainer');
    const messageEl = document.createElement('div');
    messageEl.style.textAlign = 'center';
    messageEl.style.color = '#999';
    messageEl.style.fontSize = '12px';
    messageEl.style.margin = '10px 0';
    messageEl.textContent = text;
    container.appendChild(messageEl);
    scrollToBottom();
}

// Send message
function sendMessage(event) {
    event.preventDefault();
    
    const input = document.getElementById('messageInput');
    const content = input.value.trim();

    if (!content || !currentRoom) {
        return;
    }

    // Emit message via Socket.IO
    socket.emit('send_message', {
        room_id: currentRoom.id,
        content: content
    });

    // Clear input
    input.value = '';

    // Stop typing indicator
    socket.emit('typing', { room_id: currentRoom.id, is_typing: false });
}

// Handle typing
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('messageInput');
    
    if (input) {
        input.addEventListener('input', () => {
            if (!currentRoom) return;

            // Send typing indicator
            socket.emit('typing', { room_id: currentRoom.id, is_typing: true });

            // Clear existing timeout
            clearTimeout(typingTimeout);

            // Set new timeout to stop typing indicator
            typingTimeout = setTimeout(() => {
                socket.emit('typing', { room_id: currentRoom.id, is_typing: false });
            }, 2000);
        });
    }
});

// Show typing indicator
function showTypingIndicator(isTyping) {
    const indicator = document.getElementById('typingIndicator');
    if (isTyping) {
        indicator.classList.add('active');
    } else {
        indicator.classList.remove('active');
    }
}

// Create room modal
function openCreateRoomModal() {
    document.getElementById('createRoomModal').classList.add('active');
    document.getElementById('roomNameInput').focus();
}

function closeCreateRoomModal() {
    document.getElementById('createRoomModal').classList.remove('active');
    document.getElementById('roomNameInput').value = '';
}

// Create new room
async function createRoom() {
    const nameInput = document.getElementById('roomNameInput');
    const name = nameInput.value.trim();

    if (!name) {
        showNotification('Please enter a room name', 'error');
        return;
    }

    const token = localStorage.getItem('access_token');

    try {
        const response = await fetch(`${API_URL}/chat/rooms`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: name })
        });

        if (response.ok) {
            const data = await response.json();
            showNotification('Room created successfully!', 'success');
            closeCreateRoomModal();
            
            // Reload rooms
            await loadRooms();
            
            // Auto-select the new room
            selectRoom(data.room.id, data.room.name);
        } else {
            const error = await response.json();
            showNotification(error.error || 'Failed to create room', 'error');
        }
    } catch (error) {
        console.error('Error creating room:', error);
        showNotification('Failed to create room', 'error');
    }
}

// Logout
function logout() {
    // Disconnect socket
    if (socket) {
        socket.disconnect();
    }
    
    // Clear token
    localStorage.removeItem('access_token');
    
    // Redirect to login
    window.location.href = 'login.html';
}

// Utility functions
function getInitials(firstName, lastName) {
    return (firstName.charAt(0) + lastName.charAt(0)).toUpperCase();
}

function formatTime(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 minute
    if (diff < 60000) {
        return 'Just now';
    }
    
    // Less than 1 hour
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes}m ago`;
    }
    
    // Today
    if (date.toDateString() === now.toDateString()) {
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }
    
    // This week
    if (diff < 604800000) {
        return date.toLocaleDateString('en-US', { weekday: 'short', hour: '2-digit', minute: '2-digit' });
    }
    
    // Older
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function scrollToBottom() {
    const container = document.getElementById('messagesContainer');
    setTimeout(() => {
        container.scrollTop = container.scrollHeight;
    }, 100);
}

function showNotification(message, type = 'info') {
    // Simple notification - can be enhanced with a toast library
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // You can replace this with a proper toast notification
    const color = type === 'error' ? '#f44336' : type === 'success' ? '#4caf50' : '#2196f3';
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${color};
        color: white;
        padding: 15px 20px;
        border-radius: 5px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Close modal on outside click
window.addEventListener('click', (event) => {
    const modal = document.getElementById('createRoomModal');
    if (event.target === modal) {
        closeCreateRoomModal();
    }
});

// Enter key to create room
document.addEventListener('DOMContentLoaded', () => {
    const roomNameInput = document.getElementById('roomNameInput');
    if (roomNameInput) {
        roomNameInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                createRoom();
            }
        });
    }
});
