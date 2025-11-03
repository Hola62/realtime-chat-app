// Chat Application JavaScript
const API_URL = 'http://localhost:5000';
let socket = null;
let currentRoom = null;
let currentUser = null;
let typingTimeout = null;
let roomMemberCounts = {}; // Track member counts for each room
let currentPrivateChat = null; // Track current private chat user
let isPrivateChat = false; // Track if we're in a private chat
let recentDMs = []; // Persistent recent direct messages list
let dmMetadata = {}; // Store unread counts, last message, etc. per user ID

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    // Initialize recent DMs from storage and render
    loadRecentDMs();
    loadDMMetadata();
    renderRecentDMs();
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

            // Set user avatar
            const avatarEl = document.getElementById('userAvatar');
            if (avatarEl) {
                if (data.avatar_url) {
                    avatarEl.src = `${API_URL}${data.avatar_url}`;
                } else {
                    // Show initials if no avatar
                    const initials = `${data.first_name[0]}${data.last_name[0]}`.toUpperCase();
                    avatarEl.alt = initials;
                    avatarEl.style.display = 'flex';
                    avatarEl.style.alignItems = 'center';
                    avatarEl.style.justifyContent = 'center';
                    avatarEl.style.fontSize = '16px';
                    avatarEl.style.fontWeight = 'bold';
                    avatarEl.style.color = 'white';
                }
            }

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

    // Private chat typing indicator
    socket.on('private_user_typing', (data) => {
        console.log('Private chat - user typing:', data);
        if (isPrivateChat && currentPrivateChat && data.user_id == currentPrivateChat.id) {
            showTypingIndicator(data.is_typing);
        }
    });

    // User status updates (online/offline)
    socket.on('user_status_update', (data) => {
        console.log('User status update:', data);
        if (isPrivateChat && currentPrivateChat && data.user_id == currentPrivateChat.id) {
            updatePrivateChatStatus(data.status);
        }
    });

    // Response to status check
    socket.on('user_status_response', (data) => {
        console.log('User status response:', data);
        if (isPrivateChat && currentPrivateChat && data.user_id == currentPrivateChat.id) {
            updatePrivateChatStatus(data.status);
        }
    });

    // Error handling
    socket.on('error', (data) => {
        console.error('Socket error:', data);
        showNotification(data.message || 'An error occurred', 'error');
    });

    // (AI removed)

    // Private chat events
    socket.on('private_message', (message) => {
        console.log('Private message received:', message);
        // Ensure the sender is added to recent DM list (unless it's me)
        if (message && message.user && message.user_id !== (currentUser && currentUser.id)) {
            addRecentDM({
                id: message.user_id,
                first_name: message.user.first_name,
                last_name: message.user.last_name,
                avatar_url: message.user.avatar_url
            });
            // Update metadata: last message and increment unread if not viewing this DM
            updateDMMetadata(message.user_id, message.content, message.timestamp, !isPrivateChat || currentPrivateChat?.id !== message.user_id);
        }
        if (isPrivateChat && currentPrivateChat) {
            displayMessage(message);
        }
    });

    socket.on('private_messages_history', (data) => {
        console.log('Private messages history received:', data.messages.length);
        if (isPrivateChat && currentPrivateChat) {
            displayMessageHistory(data.messages);
        }
    });

    socket.on('joined_private_chat', (data) => {
        console.log('Joined private chat:', data);
        showNotification(`Started private chat`, 'success');
    });

    socket.on('messages_read', (data) => {
        console.log('Messages marked as read:', data);
        // Update all messages in the current DM to show as read
        if (isPrivateChat && currentPrivateChat) {
            updateMessagesReadStatus(true);
        }
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

    // Exit private chat mode if active
    if (isPrivateChat && currentPrivateChat) {
        const privateRoomId = getPrivateRoomId(currentUser.id, currentPrivateChat.id);
        socket.emit('leave_private_chat', { room_id: privateRoomId });
        isPrivateChat = false;
        currentPrivateChat = null;
    }

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

    // Read status indicator for own messages in private chats
    let readStatusHTML = '';
    if (isOwn && isPrivateChat) {
        const isRead = message.read_status === true;
        const checkmark = isRead ? '✓✓' : '✓';
        const readClass = isRead ? 'read' : '';
        readStatusHTML = `<span class="message-read-status ${readClass}">${checkmark}</span>`;
    }

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
                <span class="message-time">${time}${readStatusHTML}</span>
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

    if (!content) {
        return;
    }

    // Check if we're in private chat or room chat
    if (isPrivateChat && currentPrivateChat) {
        // Regular private chat only (AI removed)
        const privateRoomId = getPrivateRoomId(currentUser.id, currentPrivateChat.id);
        socket.emit('send_private_message', {
            room_id: privateRoomId,
            other_user_id: currentPrivateChat.id,
            content: content
        });
        // Update metadata for sent message (unread=false since user is viewing)
        updateDMMetadata(currentPrivateChat.id, content, new Date().toISOString(), false);
    } else if (currentRoom) {
        // Send room message
        socket.emit('send_message', {
            room_id: currentRoom.id,
            content: content
        });
        // Stop typing indicator
        socket.emit('typing', { room_id: currentRoom.id, is_typing: false });
    } else {
        return;
    }

    // Clear input
    input.value = '';
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
            // Handle typing indicator for private chats
            if (isPrivateChat && currentPrivateChat) {
                const privateRoomId = getPrivateRoomId(currentUser.id, currentPrivateChat.id);
                socket.emit('private_typing', {
                    room_id: privateRoomId,
                    other_user_id: currentPrivateChat.id,
                    is_typing: true
                });
                clearTimeout(typingTimeout);
                typingTimeout = setTimeout(() => {
                    socket.emit('private_typing', {
                        room_id: privateRoomId,
                        other_user_id: currentPrivateChat.id,
                        is_typing: false
                    });
                }, 2000);
            }
            // Handle typing indicator for room chats
            else if (currentRoom) {
                socket.emit('typing', { room_id: currentRoom.id, is_typing: true });
                clearTimeout(typingTimeout);
                typingTimeout = setTimeout(() => {
                    socket.emit('typing', { room_id: currentRoom.id, is_typing: false });
                }, 2000);
            }
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

// --- USER SEARCH LOGIC ---
document.addEventListener('DOMContentLoaded', () => {
    // User search bar logic
    const userSearchInput = document.getElementById('userSearchInput');
    const userSearchResults = document.getElementById('userSearchResults');
    let userSearchTimeout = null;

    if (userSearchInput) {
        userSearchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            clearTimeout(userSearchTimeout);
            if (query.length < 2) {
                userSearchResults.innerHTML = '';
                return;
            }
            userSearchTimeout = setTimeout(() => {
                searchUsers(query);
            }, 300);
        });
    }

    async function searchUsers(query) {
        // Use new backend endpoint for searching users
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`${API_URL}/profile/search_users?name=${encodeURIComponent(query)}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('Failed to fetch users');
            const data = await response.json();
            renderUserSearchResults(data.users || []);
        } catch (err) {
            userSearchResults.innerHTML = '<div style="color:#f87171;padding:8px;">Error searching users</div>';
        }
    }

    function renderUserSearchResults(users) {
        if (!users.length) {
            userSearchResults.innerHTML = '<div style="color:#94a3b8;padding:8px;">No users found</div>';
            return;
        }
        userSearchResults.innerHTML = users.map(user => `
            <div class="user-search-result">
                <span class="user-search-name">${user.first_name} ${user.last_name}</span>
                <button class="user-search-message-btn" data-user-id="${user.id}">Message</button>
            </div>
        `).join('');
        // Add click handlers
        userSearchResults.querySelectorAll('.user-search-message-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const userId = btn.getAttribute('data-user-id');
                const user = users.find(u => u.id == userId);
                if (user) startPrivateChat(user);
            });
        });
    }
});

// Start a private chat with a user
function startPrivateChat(user) {
    console.log('Starting private chat with:', user);

    // Leave current room if any
    if (currentRoom) {
        socket.emit('leave_room', { room_id: currentRoom.id });
        currentRoom = null;
    }

    // Set private chat mode
    isPrivateChat = true;
    currentPrivateChat = user;

    // Clear room selection
    document.querySelectorAll('.room-item').forEach(item => {
        item.classList.remove('active');
    });
    // Also clear any active DM selection
    document.querySelectorAll('.dm-item').forEach(item => item.classList.remove('active'));
    // Highlight this user in the DM list
    setActiveDM(user.id);

    // Hide welcome screen, show chat area
    document.getElementById('welcomeScreen').style.display = 'none';
    const chatArea = document.getElementById('chatArea');
    chatArea.className = 'chat-area-visible';

    // Update chat header with user name and status
    document.getElementById('currentRoomName').textContent = `${user.first_name} ${user.last_name}`;

    // Show online/offline status (will be updated by socket event)
    updatePrivateChatStatus('checking...');

    // Clear messages
    const container = document.getElementById('messagesContainer');
    const regularMessages = container.querySelectorAll('.message');
    regularMessages.forEach(msg => msg.remove());

    // Join private Socket.IO room
    const privateRoomId = getPrivateRoomId(currentUser.id, user.id);
    console.log('Joining private room:', privateRoomId);
    socket.emit('join_private_chat', {
        room_id: privateRoomId,
        other_user_id: user.id
    });

    // Request user status
    socket.emit('check_user_status', { user_id: user.id });

    // Load private message history
    socket.emit('get_private_messages', {
        room_id: privateRoomId,
        other_user_id: user.id,
        limit: 50
    });

    // Persist in recent DMs and re-render list
    addRecentDM(user);

    // Clear search
    document.getElementById('userSearchInput').value = '';
    document.getElementById('userSearchResults').innerHTML = '';

    // Reset unread count for this DM
    clearUnreadForDM(user.id);
}

// Start a private chat with the AI assistant
// (startAiChat removed)

// Update private chat status indicator
function updatePrivateChatStatus(status) {
    const statusEl = document.getElementById('connectionStatus');
    if (isPrivateChat && currentPrivateChat) {
        if (status === 'online') {
            statusEl.innerHTML = '● Online';
            statusEl.className = 'chat-status status-online';
        } else if (status === 'offline') {
            statusEl.innerHTML = '● Offline';
            statusEl.className = 'chat-status';
            statusEl.style.color = '#94a3b8';
        } else {
            statusEl.innerHTML = `● ${status}`;
            statusEl.className = 'chat-status';
            statusEl.style.color = '#94a3b8';
        }
    }
}

// Get a consistent private room ID for two users
function getPrivateRoomId(userId1, userId2) {
    // Always use lower ID first to ensure consistency
    const ids = [parseInt(userId1), parseInt(userId2)].sort((a, b) => a - b);
    return `private_${ids[0]}_${ids[1]}`;
}

// ======================
// Recent DMs persistence
// ======================

function loadRecentDMs() {
    try {
        const raw = localStorage.getItem('recent_dms');
        const list = raw ? JSON.parse(raw) : [];
        if (Array.isArray(list)) {
            recentDMs = list;
        } else {
            recentDMs = [];
        }
    } catch {
        recentDMs = [];
    }
    // Remove self if present
    if (currentUser) {
        recentDMs = recentDMs.filter(u => u && u.id !== currentUser.id);
    }
}

function saveRecentDMs() {
    try {
        localStorage.setItem('recent_dms', JSON.stringify(recentDMs.slice(0, 20)));
    } catch { }
}

function addRecentDM(user) {
    if (!user || !user.id) return;
    if (currentUser && user.id === currentUser.id) return; // skip self
    // Deduplicate by id, move to front
    const id = parseInt(user.id);
    const existingIdx = recentDMs.findIndex(u => parseInt(u.id) === id);
    if (existingIdx !== -1) {
        recentDMs.splice(existingIdx, 1);
    }
    recentDMs.unshift({
        id: id,
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        avatar_url: user.avatar_url || null
    });
    // Cap size
    if (recentDMs.length > 20) recentDMs.length = 20;
    saveRecentDMs();
    renderRecentDMs();
}

// DM Metadata (unread count, last message, time)
function loadDMMetadata() {
    try {
        const raw = localStorage.getItem('dm_metadata');
        dmMetadata = raw ? JSON.parse(raw) : {};
    } catch {
        dmMetadata = {};
    }
}

function saveDMMetadata() {
    try {
        localStorage.setItem('dm_metadata', JSON.stringify(dmMetadata));
    } catch { }
}

function updateDMMetadata(userId, lastMessage, timestamp, incrementUnread = false) {
    const uid = String(userId);
    if (!dmMetadata[uid]) {
        dmMetadata[uid] = { unread: 0, lastMessage: '', lastTime: null };
    }
    dmMetadata[uid].lastMessage = (lastMessage || '').substring(0, 50);
    dmMetadata[uid].lastTime = timestamp;
    if (incrementUnread) {
        dmMetadata[uid].unread = (dmMetadata[uid].unread || 0) + 1;
    }
    saveDMMetadata();
    renderRecentDMs();
}

function clearUnreadForDM(userId) {
    const uid = String(userId);
    if (dmMetadata[uid]) {
        dmMetadata[uid].unread = 0;
        saveDMMetadata();
        renderRecentDMs();
    }
}

function formatRelativeTime(ts) {
    if (!ts) return '';
    try {
        const msgDate = new Date(ts);
        const now = new Date();
        const diffMs = now - msgDate;
        const diffMins = Math.floor(diffMs / 60000);
        if (diffMins < 1) return 'now';
        if (diffMins < 60) return `${diffMins}m`;
        const diffHrs = Math.floor(diffMins / 60);
        if (diffHrs < 24) return `${diffHrs}h`;
        const diffDays = Math.floor(diffHrs / 24);
        if (diffDays < 7) return `${diffDays}d`;
        return msgDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
        return '';
    }
}

function renderRecentDMs() {
    const el = document.getElementById('dmList');
    if (!el) return;
    if (!recentDMs.length) {
        el.innerHTML = '<div style="color:#94a3b8;padding:8px 16px;">No direct messages yet</div>';
        return;
    }
    el.innerHTML = recentDMs.map(u => {
        const initials = getInitials(u.first_name, u.last_name);
        const name = `${escapeHtml(u.first_name)} ${escapeHtml(u.last_name)}`.trim();
        const avatar = u.avatar_url ? `<img src="${API_URL}${u.avatar_url}" alt="${name}" onerror="this.parentElement.textContent='${initials}'">` : initials;

        const uid = String(u.id);
        const meta = dmMetadata[uid] || { unread: 0, lastMessage: '', lastTime: null };
        const unreadBadge = meta.unread > 0 ? `<span class="dm-unread">${meta.unread}</span>` : '';
        const preview = meta.lastMessage ? escapeHtml(meta.lastMessage) : 'No messages yet';
        const timeStr = formatRelativeTime(meta.lastTime);

        return `
            <div class="dm-item" data-user-id="${u.id}">
                <div class="dm-avatar">${avatar}</div>
                <div class="dm-info">
                    <div class="dm-name">${name || 'Unknown User'}</div>
                    <div class="dm-preview">${preview}</div>
                </div>
                <div class="dm-meta">
                    <div class="dm-time">${timeStr}</div>
                    ${unreadBadge}
                </div>
            </div>
        `;
    }).join('');

    // Click handlers
    el.querySelectorAll('.dm-item').forEach(item => {
        item.addEventListener('click', () => {
            const uid = parseInt(item.getAttribute('data-user-id'));
            const u = recentDMs.find(x => parseInt(x.id) === uid);
            if (u) startPrivateChat(u);
        });
    });

    // Maintain active highlight if applicable
    if (isPrivateChat && currentPrivateChat) {
        setActiveDM(currentPrivateChat.id);
    }
}

function setActiveDM(userId) {
    document.querySelectorAll('.dm-item').forEach(i => i.classList.remove('active'));
    const item = document.querySelector(`.dm-item[data-user-id="${userId}"]`);
    if (item) item.classList.add('active');
}

// ======================
// Helpers (fix undefined)
// ======================

function escapeHtml(unsafe) {
    if (unsafe === null || unsafe === undefined) return '';
    return String(unsafe)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function getInitials(first, last) {
    const f = (first || '').trim();
    const l = (last || '').trim();
    const fi = f ? f[0].toUpperCase() : '';
    const li = l ? l[0].toUpperCase() : '';
    return (fi + li) || '??';
}

function formatTime(ts) {
    try {
        if (!ts) return '';
        const d = new Date(ts);
        if (isNaN(d.getTime())) return '';
        const hh = d.getHours().toString().padStart(2, '0');
        const mm = d.getMinutes().toString().padStart(2, '0');
        return `${hh}:${mm}`;
    } catch { return ''; }
}

function scrollToBottom() {
    const el = document.getElementById('messagesContainer');
    if (!el) return;
    el.scrollTop = el.scrollHeight;
}

function updateMessagesReadStatus(isRead) {
    // Update all own messages in the current chat to show read status
    const container = document.getElementById('messagesContainer');
    if (!container) return;

    const ownMessages = container.querySelectorAll('.message.own .message-read-status');
    ownMessages.forEach(statusEl => {
        if (isRead) {
            statusEl.textContent = '✓✓';
            statusEl.classList.add('read');
        } else {
            statusEl.textContent = '✓';
            statusEl.classList.remove('read');
        }
    });
}

function showNotification(message, type = 'info') {
    // Lightweight toast
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed; left: 50%; transform: translateX(-50%);
        bottom: 24px; padding: 10px 16px; border-radius: 8px;
        background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6'};
        color: #fff; font-weight: 600; box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        z-index: 10000; opacity: 0; transition: opacity .2s ease-in;
    `;
    document.body.appendChild(toast);
    requestAnimationFrame(() => { toast.style.opacity = '1'; });
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 250);
    }, 2000);
}
