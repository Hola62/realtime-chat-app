// Chat Application JavaScript
const API_URL = 'http://localhost:5000';
let socket = null;
let currentRoom = null;
let currentUser = null;
let typingTimeout = null;
let roomMemberCounts = {}; // Track member counts for each room

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
});

// Check if user is authenticated
function checkAuth() {
    const token = localStorage.getItem('access_token');
    console.log('checkAuth: token exists?', !!token);

    if (!token) {
        console.log('No token found, redirecting to login');
        window.location.href = 'login.html';
        return;
    }

    console.log('Token found, fetching user info...');
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
        console.log('Fetching user info from:', `${API_URL}/auth/me`);
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        console.log('Response status:', response.status);

        if (response.ok) {
            const data = await response.json();
            console.log('User data received:', data);
            currentUser = data;

            // Check if required fields exist
            if (!data.first_name || !data.last_name || !data.email) {
                console.error('Missing required user fields:', data);
                showNotification('Incomplete user data received', 'error');
                return;
            }

            document.getElementById('userName').textContent = `${data.first_name} ${data.last_name}`;
            document.getElementById('userEmail').textContent = data.email;
            console.log('User info displayed successfully');
        } else {
            // Token invalid, redirect to login
            console.log('Token invalid or server error, logging out');
            const errorData = await response.json().catch(() => ({}));
            console.error('Error response:', errorData);
            logout();
        }
    } catch (error) {
        console.error('Error fetching user info:', error);
        showNotification('Failed to load user information', 'error');
        // Don't logout on network errors, just show error
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

        // Notify server that user is online
        socket.emit('user_online');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        updateConnectionStatus(false);
    });

    socket.on('connected', (data) => {
        console.log('Server confirmation:', data);
    });

    // User status events
    socket.on('user_status_changed', (data) => {
        console.log('User status changed:', data);
        updateUserStatusUI(data.user_id, data.status, data.user);
    });

    // Room events
    socket.on('joined_room', (data) => {
        console.log('Joined room:', data);
        // Update member count for this room
        if (data.member_count !== undefined) {
            roomMemberCounts[data.room_id] = data.member_count;
            updateRoomMemberCount(data.room_id, data.member_count);
        }
        // Don't show notification when switching rooms - it's less intrusive
        // User already knows they're joining a room by clicking on it
    });

    socket.on('user_joined', (data) => {
        console.log('User joined:', data);
        // Update member count
        if (data.member_count !== undefined) {
            roomMemberCounts[data.room_id] = data.member_count;
            updateRoomMemberCount(data.room_id, data.member_count);
        }
        addSystemMessage(`A user joined the room`);
    });

    socket.on('user_left', (data) => {
        console.log('User left:', data);
        // Update member count
        if (data.member_count !== undefined) {
            roomMemberCounts[data.room_id] = data.member_count;
            updateRoomMemberCount(data.room_id, data.member_count);
        }
        addSystemMessage(`A user left the room`);
    });

    socket.on('left_room', (data) => {
        console.log('Left room:', data);
    });

    // Message events
    socket.on('new_message', (message) => {
        console.log('New message received:', message);
        console.log('Current room:', currentRoom);

        // Display message - Socket.IO room membership handles filtering
        displayMessage(message);
    });

    socket.on('messages_history', (data) => {
        console.log('=== Message History Received ===');
        console.log('Room ID:', data.room_id);
        console.log('Number of messages:', data.messages.length);
        console.log('Current room:', currentRoom);

        // Only display if it's for the current room
        if (currentRoom && data.room_id === currentRoom.id) {
            console.log('Displaying messages for current room');
            displayMessageHistory(data.messages);
        } else {
            console.log('Ignoring messages - not for current room');
        }
    });

    // Message deletion events
    socket.on('message_deleted', (data) => {
        console.log('Message deleted:', data);
        const messageEl = document.querySelector(`[data-message-id="${data.message_id}"]`);
        if (messageEl) {
            messageEl.innerHTML = `
                <div class="message-avatar"></div>
                <div class="message-content">
                    <div class="message-bubble" style="background: #f3f4f6; color: #9ca3af; font-style: italic; border: 1px dashed #d1d5db;">
                        This message was deleted
                    </div>
                </div>
            `;
            messageEl.style.opacity = '0.6';
        }
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

    roomsList.innerHTML = rooms.map(room => {
        const isCreator = currentUser && room.created_by === currentUser.id;
        const deleteBtn = isCreator ?
            `<button class="delete-room-btn" onclick="event.stopPropagation(); deleteRoom(${room.id}, '${room.name.replace(/'/g, "\\'")}')">Delete</button>` :
            '';

        const memberCount = roomMemberCounts[room.id] || 0;
        const memberText = memberCount === 1 ? 'member' : 'members';

        return `
            <div class="room-item" data-room-id="${room.id}" onclick="selectRoom(${room.id}, '${room.name.replace(/'/g, "\\'")}')">
                <div class="room-info">
                    <div class="room-name">${escapeHtml(room.name)}</div>
                    <div class="room-creator">
                        <span>Created by ${escapeHtml(room.creator.first_name)} ${escapeHtml(room.creator.last_name)}</span>
                        <span class="room-members" data-room-id="${room.id}">
                            ${memberCount > 0 ? `• ${memberCount} ${memberText}` : ''}
                        </span>
                    </div>
                </div>
                ${deleteBtn}
            </div>
        `;
    }).join('');
}

// Update room member count display
function updateRoomMemberCount(roomId, count) {
    const memberSpan = document.querySelector(`.room-members[data-room-id="${roomId}"]`);
    if (memberSpan) {
        const memberText = count === 1 ? 'member' : 'members';
        memberSpan.textContent = count > 0 ? `• ${count} ${memberText}` : '';
    }

    // Also update the chat header if we're in this room
    if (currentRoom && currentRoom.id === roomId) {
        updateChatHeaderMemberCount(count);
    }
}

// Update member count in chat header
function updateChatHeaderMemberCount(count) {
    const memberText = count === 1 ? 'member' : 'members';
    const chatStatus = document.querySelector('.chat-status');
    if (chatStatus) {
        chatStatus.textContent = count > 0 ? `${count} ${memberText}` : '';
    }
}

// Select a room
function selectRoom(roomId, roomName) {
    console.log('=== Selecting Room ===');
    console.log('New room:', roomId, roomName);
    console.log('Previous room:', currentRoom);

    // Leave current room if any
    if (currentRoom) {
        console.log('Leaving room:', currentRoom.id);
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

    // Clear only regular messages, keep system messages
    const container = document.getElementById('messagesContainer');
    const regularMessages = container.querySelectorAll('.message');
    regularMessages.forEach(msg => msg.remove());

    console.log('Joining room:', roomId);
    // Join room via Socket.IO
    socket.emit('join_room', { room_id: roomId });

    console.log('Requesting message history for room:', roomId);
    // Load message history
    socket.emit('get_messages', { room_id: roomId, limit: 50 });
}

// Display message history
function displayMessageHistory(messages) {
    console.log('=== Displaying Message History ===');
    console.log('Number of messages to display:', messages.length);

    const container = document.getElementById('messagesContainer');

    // Remove only regular messages, keep system messages
    const allMessages = container.querySelectorAll('.message');
    console.log('Removing', allMessages.length, 'existing messages');
    allMessages.forEach(msg => msg.remove());

    messages.forEach((message, index) => {
        console.log(`Displaying message ${index + 1}:`, message.content?.substring(0, 30));
        displayMessage(message, false);
    });

    console.log('Message history display complete');
    // Scroll to bottom
    scrollToBottom();
}

// Display a single message
function displayMessage(message, animate = true) {
    const container = document.getElementById('messagesContainer');
    const isOwn = currentUser && message.user_id === currentUser.id;

    const messageEl = document.createElement('div');
    messageEl.className = `message ${isOwn ? 'own' : ''}`;
    messageEl.dataset.messageId = message.id;
    if (!animate) messageEl.style.animation = 'none';

    // Check if message is deleted
    if (message.deleted) {
        messageEl.innerHTML = `
            <div class="message-avatar"></div>
            <div class="message-content">
                <div class="message-bubble" style="background: #f3f4f6; color: #9ca3af; font-style: italic; border: 1px dashed #d1d5db;">
                    This message was deleted
                </div>
            </div>
        `;
        messageEl.style.opacity = '0.6';
        container.appendChild(messageEl);
        scrollToBottom();
        return;
    }

    const initials = getInitials(message.user.first_name, message.user.last_name);
    const senderName = `${message.user.first_name} ${message.user.last_name}`;
    const time = formatTime(message.timestamp);

    // Debug: Log avatar URL
    console.log('Message user data:', message.user);
    console.log('Avatar URL:', message.user.avatar_url);

    // Get avatar - use profile picture if available, otherwise show initials
    const avatarContent = message.user.avatar_url
        ? `<img src="${API_URL}${message.user.avatar_url}" alt="${escapeHtml(senderName)}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;" onerror="this.parentElement.textContent='${initials}'">`
        : initials;

    messageEl.innerHTML = `
        <div class="message-avatar">${avatarContent}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-sender">${escapeHtml(senderName)}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-bubble" data-original-content="${escapeHtml(message.content)}">
                ${escapeHtml(message.content)}
            </div>
        </div>
    `;

    // Add long-press functionality
    let pressTimer;
    const messageBubble = messageEl.querySelector('.message-bubble');

    // Mouse events
    messageBubble.addEventListener('mousedown', (e) => {
        pressTimer = setTimeout(() => {
            showMessageMenu(message.id, isOwn, e.clientX, e.clientY, message.content);
        }, 500); // 500ms long press
    });

    messageBubble.addEventListener('mouseup', () => {
        clearTimeout(pressTimer);
    });

    messageBubble.addEventListener('mouseleave', () => {
        clearTimeout(pressTimer);
    });

    // Touch events for mobile
    messageBubble.addEventListener('touchstart', (e) => {
        pressTimer = setTimeout(() => {
            const touch = e.touches[0];
            showMessageMenu(message.id, isOwn, touch.clientX, touch.clientY, message.content);
        }, 500);
    });

    messageBubble.addEventListener('touchend', () => {
        clearTimeout(pressTimer);
    });

    container.appendChild(messageEl);
    scrollToBottom();
}

// Add system message
function addSystemMessage(text) {
    const container = document.getElementById('messagesContainer');
    const messageEl = document.createElement('div');
    messageEl.className = 'system-message'; // Add class to identify system messages
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

// Show message context menu
function showMessageMenu(messageId, isOwn, x, y, content) {
    // Remove any existing menu
    const existingMenu = document.querySelector('.message-context-menu');
    if (existingMenu) {
        existingMenu.remove();
    }

    // Create menu
    const menu = document.createElement('div');
    menu.className = 'message-context-menu';
    menu.style.cssText = `
        position: fixed;
        left: ${x}px;
        top: ${y}px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        padding: 8px 0;
        z-index: 10000;
        min-width: 150px;
        animation: menuSlideIn 0.2s ease-out;
    `;

    // Menu options
    const options = [];

    // React option (for all messages)
    options.push({
        label: 'React',
        icon: '',
        action: () => {
            closeMessageMenu();
            reactToMessage(messageId);
        }
    });

    // Copy option (for all messages)
    options.push({
        label: 'Copy',
        icon: '',
        action: () => {
            navigator.clipboard.writeText(content);
            closeMessageMenu();
            showNotification('Message copied!', 'success');
        }
    });

    // Edit and Delete only for own messages
    if (isOwn) {
        options.push({
            label: 'Edit',
            icon: '',
            action: () => {
                closeMessageMenu();
                editMessage(messageId, content);
            }
        });

        options.push({
            label: 'Delete',
            icon: '',
            action: () => {
                closeMessageMenu();
                deleteMessage(messageId);
            }
        });
    }

    // Create menu items
    options.forEach(option => {
        const item = document.createElement('div');
        item.className = 'menu-item';
        item.innerHTML = option.label;
        item.style.cssText = `
            padding: 10px 20px;
            cursor: pointer;
            transition: background 0.2s;
            display: flex;
            align-items: center;
            gap: 10px;
        `;
        item.addEventListener('mouseenter', () => {
            item.style.background = '#f5f5f5';
        });
        item.addEventListener('mouseleave', () => {
            item.style.background = 'transparent';
        });
        item.addEventListener('click', option.action);
        menu.appendChild(item);
    });

    document.body.appendChild(menu);

    // Adjust menu position if it goes off screen
    const menuRect = menu.getBoundingClientRect();
    if (menuRect.right > window.innerWidth) {
        menu.style.left = (x - menuRect.width) + 'px';
    }
    if (menuRect.bottom > window.innerHeight) {
        menu.style.top = (y - menuRect.height) + 'px';
    }

    // Close menu when clicking outside
    setTimeout(() => {
        document.addEventListener('click', closeMessageMenu);
    }, 100);
}

// Close message menu
function closeMessageMenu() {
    const menu = document.querySelector('.message-context-menu');
    if (menu) {
        menu.style.animation = 'menuSlideOut 0.2s ease-out';
        setTimeout(() => menu.remove(), 200);
    }
    document.removeEventListener('click', closeMessageMenu);
}

// Edit message
function editMessage(messageId, currentContent) {

    const newContent = prompt('Edit your message:', currentContent);

    if (newContent === null || newContent.trim() === '') {
        return; // User cancelled or entered empty message
    }

    if (newContent.trim() === currentContent) {
        return; // No changes made
    }

    // Find the message element and update it locally (optimistic update)
    const messageEl = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageEl) {
        const bubble = messageEl.querySelector('.message-bubble');
        bubble.textContent = newContent.trim() + ' (edited)';
        bubble.style.fontStyle = 'italic';
    }

    showNotification('Message updated (edit feature is UI-only for now)', 'success');
}

// Delete message
function deleteMessage(messageId) {
    if (!confirm('Are you sure you want to delete this message?')) {
        return;
    }

    // Send delete request to server
    socket.emit('delete_message', {
        message_id: messageId,
        room_id: currentRoom.id
    });

    // Optimistically remove from UI
    const messageEl = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageEl) {
        messageEl.style.animation = 'fadeOut 0.3s';
        setTimeout(() => {
            // Replace with "deleted" placeholder
            messageEl.innerHTML = `
                <div class="message-avatar"></div>
                <div class="message-content">
                    <div class="message-bubble" style="background: #f3f4f6; color: #9ca3af; font-style: italic; border: 1px dashed #d1d5db;">
                        This message was deleted
                    </div>
                </div>
            `;
            messageEl.style.animation = 'none';
            messageEl.style.opacity = '0.6';
        }, 300);
    }
}

// React to message
function reactToMessage(messageId) {
    const reactions = ['❤️', '👍', '😂', '😮', '😢', '🎉'];
    const reaction = prompt(`React to this message:\n\n${reactions.join('  ')}\n\nEnter emoji or choose from above:`, '❤️');

    if (!reaction) {
        return;
    }

    // Find message and add reaction
    const messageEl = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageEl) {
        let reactionsDiv = messageEl.querySelector('.message-reactions');
        if (!reactionsDiv) {
            reactionsDiv = document.createElement('div');
            reactionsDiv.className = 'message-reactions';
            reactionsDiv.style.cssText = 'margin-top: 5px; font-size: 14px;';
            messageEl.querySelector('.message-content').appendChild(reactionsDiv);
        }

        const reactionSpan = document.createElement('span');
        reactionSpan.textContent = reaction + ' ';
        reactionSpan.style.marginRight = '5px';
        reactionsDiv.appendChild(reactionSpan);

        showNotification('Reaction added (react feature is UI-only for now)', 'success');
    }
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

// Delete a room
async function deleteRoom(roomId, roomName) {
    // Confirm before deleting
    if (!confirm(`Are you sure you want to delete the room "${roomName}"?\n\nThis will delete all messages in this room and cannot be undone.`)) {
        return;
    }

    const token = localStorage.getItem('access_token');

    try {
        const response = await fetch(`${API_URL}/chat/rooms/${roomId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            showNotification('Room deleted successfully!', 'success');

            // If we were in the deleted room, clear the chat
            if (currentRoom && currentRoom.id === roomId) {
                currentRoom = null;
                document.getElementById('chatArea').style.display = 'none';
                document.getElementById('welcomeScreen').style.display = 'flex';
            }

            // Reload rooms list
            await loadRooms();
        } else {
            const error = await response.json();
            showNotification(error.message || 'Failed to delete room', 'error');
        }
    } catch (error) {
        console.error('Error deleting room:', error);
        showNotification('Failed to delete room', 'error');
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

// Update user status in UI
function updateUserStatusUI(userId, status, user) {
    console.log(`User ${userId} is now ${status}`);
    // Future enhancement: show online/offline indicators in UI
    // Can be used to update user list, show green/gray dots next to names, etc.
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
