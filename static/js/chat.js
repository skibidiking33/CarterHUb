// Chat application JavaScript with Socket.IO integration

let socket;
let currentChatUser = null;
let currentChatGroup = null;
let searchTimeout = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Socket.IO
    socket = io();
    
    // Socket event handlers
    socket.on('connect', function() {
        console.log('Connected to chat server');
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from chat server');
    });
    
    socket.on('new_message', function(data) {
        displayMessage(data);
    });
    
    socket.on('messages_history', function(data) {
        displayMessagesHistory(data.messages);
    });
    
    // Initialize chat functionality
    initializeChat();
});

function initializeChat() {
    // Search functionality
    const searchInput = document.getElementById('user-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    searchUsers(query);
                }, 300);
            } else {
                hideSearchResults();
            }
        });
    }
    
    // Message input functionality
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
}

function openPrivateChat(userId, username) {
    currentChatUser = userId;
    currentChatGroup = null;
    
    // Update UI
    updateChatHeader(`Chat with ${username}`);
    clearChatArea();
    enableMessageInput();
    
    // Mark as active
    document.querySelectorAll('.friend-item, .group-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-user-id="${userId}"]`).classList.add('active');
    
    // Load message history
    socket.emit('get_messages', { chat_with: userId });
}

function openGroupChat(groupId, groupName) {
    currentChatGroup = groupId;
    currentChatUser = null;
    
    // Update UI
    updateChatHeader(`Group: ${groupName}`);
    clearChatArea();
    enableMessageInput();
    
    // Mark as active
    document.querySelectorAll('.friend-item, .group-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-group-id="${groupId}"]`).classList.add('active');
    
    // Load message history
    socket.emit('get_messages', { group_id: groupId });
}

function updateChatHeader(title) {
    const chatArea = document.getElementById('chat-area');
    chatArea.innerHTML = `
        <div class="text-center text-muted py-3 border-bottom">
            <h6 class="mb-0">${title}</h6>
        </div>
        <div id="messages-container"></div>
    `;
}

function clearChatArea() {
    const messagesContainer = document.getElementById('messages-container');
    if (messagesContainer) {
        messagesContainer.innerHTML = '';
    }
}

function enableMessageInput() {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const inputArea = document.getElementById('message-input-area');
    
    if (inputArea) inputArea.style.display = 'block';
    if (messageInput) messageInput.disabled = false;
    if (sendButton) sendButton.disabled = false;
    
    if (messageInput) {
        messageInput.placeholder = currentChatUser 
            ? 'Type a message...' 
            : 'Message the group...';
    }
}

function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const content = messageInput.value.trim();
    
    if (!content) return;
    
    // Check if it's a group command
    if (content.startsWith('/')) {
        handleGroupCommand(content);
        messageInput.value = '';
        return;
    }
    
    const messageData = {
        content: content
    };
    
    if (currentChatUser) {
        messageData.receiver_id = currentChatUser;
    } else if (currentChatGroup) {
        messageData.group_id = currentChatGroup;
    } else {
        return;
    }
    
    socket.emit('send_message', messageData);
    messageInput.value = '';
}

function handleGroupCommand(command) {
    fetch('/handle_group_command', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            command: command
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            // If user joined a group, refresh the page to show the new group
            if (command.startsWith('/accept')) {
                setTimeout(() => {
                    location.reload();
                }, 1500);
            }
        } else {
            showNotification(data.error || 'Command failed', 'danger');
        }
    })
    .catch(error => {
        console.error('Error handling command:', error);
        showNotification('Failed to execute command', 'danger');
    });
}

function displayMessage(message) {
    const messagesContainer = document.getElementById('messages-container');
    if (!messagesContainer) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${message.is_own ? 'own-message' : ''}`;
    
    messageElement.innerHTML = `
        <div class="message-header">
            <span class="message-username">${message.sender_username}</span>
            <span class="message-timestamp">${message.timestamp}</span>
        </div>
        <div class="message-content">${escapeHtml(message.content)}</div>
    `;
    
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function displayMessagesHistory(messages) {
    const messagesContainer = document.getElementById('messages-container');
    if (!messagesContainer) return;
    
    messagesContainer.innerHTML = '';
    
    messages.forEach(message => {
        displayMessage(message);
    });
}

function searchUsers(query) {
    fetch(`/search_users?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(users => {
            displaySearchResults(users);
        })
        .catch(error => {
            console.error('Search error:', error);
        });
}

function displaySearchResults(users) {
    const resultsContainer = document.getElementById('search-results');
    if (!resultsContainer) return;
    
    if (users.length === 0) {
        resultsContainer.style.display = 'none';
        return;
    }
    
    resultsContainer.innerHTML = '';
    
    users.forEach(user => {
        const resultItem = document.createElement('div');
        resultItem.className = 'search-result-item';
        
        let actionButton = '';
        if (user.is_friend) {
            actionButton = '<span class="badge bg-success">Friends</span>';
        } else if (user.has_pending_request) {
            actionButton = '<span class="badge bg-warning">Pending</span>';
        } else {
            actionButton = `<button class="btn btn-sm btn-discord" onclick="sendFriendRequest(${user.id})">Add Friend</button>`;
        }
        
        resultItem.innerHTML = `
            <div>
                <i class="fas fa-user me-2"></i>
                <span>${escapeHtml(user.username)}</span>
            </div>
            <div>${actionButton}</div>
        `;
        
        resultsContainer.appendChild(resultItem);
    });
    
    resultsContainer.style.display = 'block';
}

function hideSearchResults() {
    const resultsContainer = document.getElementById('search-results');
    if (resultsContainer) {
        resultsContainer.style.display = 'none';
    }
}

function sendFriendRequest(userId) {
    fetch(`/send_friend_request/${userId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Friend request sent!', 'success');
            // Refresh search results
            const searchInput = document.getElementById('user-search');
            if (searchInput && searchInput.value.trim()) {
                searchUsers(searchInput.value.trim());
            }
        } else {
            showNotification(data.error || 'Failed to send friend request', 'danger');
        }
    })
    .catch(error => {
        console.error('Error sending friend request:', error);
        showNotification('Failed to send friend request', 'danger');
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showCreateGroupModal() {
    const modal = new bootstrap.Modal(document.getElementById('createGroupModal'));
    modal.show();
}

function createGroup() {
    const name = document.getElementById('groupName').value.trim();
    const description = document.getElementById('groupDescription').value.trim();
    
    if (!name) {
        showNotification('Please enter a group name', 'danger');
        return;
    }
    
    fetch('/create_group', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: name,
            description: description
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Group created successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('createGroupModal')).hide();
            location.reload();
        } else {
            showNotification(data.error || 'Failed to create group', 'danger');
        }
    })
    .catch(error => {
        console.error('Error creating group:', error);
        showNotification('Failed to create group', 'danger');
    });
}

let selectedGroupId = null;

function showAddToGroupModal(groupId, groupName) {
    console.log('Opening add to group modal for group:', groupId, groupName);
    selectedGroupId = groupId;
    
    const groupNameDisplay = document.getElementById('groupNameDisplay');
    if (groupNameDisplay) {
        groupNameDisplay.textContent = groupName;
    }
    
    // Show loading message
    const friendsContainer = document.getElementById('friendsToAdd');
    if (friendsContainer) {
        friendsContainer.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin me-2"></i>Loading friends...</div>';
    }
    
    // Show the modal first
    const modalElement = document.getElementById('addToGroupModal');
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        
        // Then fetch friends list
        fetch('/get_friends')
        .then(response => response.json())
        .then(data => {
            if (friendsContainer) {
                friendsContainer.innerHTML = '';
                
                if (data.friends && data.friends.length > 0) {
                    data.friends.forEach(friend => {
                        const friendItem = document.createElement('div');
                        friendItem.className = 'friend-invite-item d-flex justify-content-between align-items-center p-2 mb-2 bg-secondary rounded';
                        friendItem.innerHTML = `
                            <div class="d-flex align-items-center">
                                <i class="fas fa-user me-2"></i>
                                <span>${escapeHtml(friend.username)}</span>
                                <div class="status-indicator ms-2 ${friend.is_online ? 'status-online' : 'status-offline'}"></div>
                            </div>
                            <button class="btn btn-sm btn-discord invite-btn-${friend.id}" onclick="sendGroupInvite(${friend.id}, '${escapeHtml(friend.username)}')">
                                <i class="fas fa-paper-plane me-1"></i>Invite
                            </button>
                        `;
                        friendsContainer.appendChild(friendItem);
                    });
                } else {
                    friendsContainer.innerHTML = '<p class="text-muted text-center">No friends available to invite.</p>';
                }
            }
        })
        .catch(error => {
            console.error('Error fetching friends:', error);
            if (friendsContainer) {
                friendsContainer.innerHTML = '<p class="text-danger text-center">Failed to load friends list.</p>';
            }
            showNotification('Failed to load friends list', 'danger');
        });
    } else {
        console.error('Modal element not found');
        showNotification('Modal not found', 'danger');
    }
}

function sendGroupInvite(friendId, friendUsername) {
    console.log('Sending group invite to friend:', friendId, friendUsername);
    
    // Find the button and disable it immediately to prevent double-clicks
    const button = document.querySelector(`.invite-btn-${friendId}`);
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Sending...';
    }
    
    fetch('/send_group_invite', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            group_id: selectedGroupId,
            friend_id: friendId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            if (button) {
                button.innerHTML = '<i class="fas fa-check me-1"></i>Sent';
                button.classList.remove('btn-discord');
                button.classList.add('btn-success');
            }
        } else {
            showNotification(data.error || 'Failed to send group invitation', 'danger');
            if (button) {
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-paper-plane me-1"></i>Invite';
            }
        }
    })
    .catch(error => {
        console.error('Error sending group invitation:', error);
        showNotification('Failed to send group invitation', 'danger');
        if (button) {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-paper-plane me-1"></i>Invite';
        }
    });
}

function addSelectedFriends() {
    // This function is no longer needed but kept for compatibility
    showNotification('Use individual invite buttons to send group invitations!', 'info');
}

function showNotification(message, type = 'success') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}
