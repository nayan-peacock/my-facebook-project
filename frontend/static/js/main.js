// Use a relative path for the API
const API_URL = '/api';
let authToken = localStorage.getItem('authToken');
let currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
// Connect to the same server that's serving the file
let socket = io();

function showNotification(message, type = 'success') {
    const notif = document.createElement('div');
    notif.className = 'notification';
    notif.textContent = message;
    notif.style.background = type === 'success' ? '#31a24c' : '#f02849';
    notif.style.color = 'white';
    document.body.appendChild(notif);
    setTimeout(() => notif.remove(), 3000);
}

/**
 * This function builds all API requests.
 * Notice how it adds the 'Authorization': `Bearer ${authToken}` header.
 * If authToken is null, this header is invalid, causing the 422 error.
 */
async function apiRequest(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}` // <-- This requires authToken to be set
        }
    };
    
    if (body) {
        options.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(`${API_URL}${endpoint}`, options);
        const data = await response.json();
        
        if (!response.ok) {
            // This is where "Request fail" was coming from
            throw new Error(data.message || 'Request failed'); 
        }
        
        return data;
    } catch (error) {
        showNotification(error.message, 'error');
        throw error;
    }
}

function showLoginForm() {
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('registerForm').style.display = 'none';
}

function showRegisterForm() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
}

async function register() {
    const data = {
        first_name: document.getElementById('regFirstName').value,
        last_name: document.getElementById('regLastName').value,
        email: document.getElementById('regEmail').value,
        username: document.getElementById('regUsername').value,
        password: document.getElementById('regPassword').value,
        birth_date: document.getElementById('regBirthDate').value,
        gender: document.getElementById('regGender').value
    };

    try {
        // Register doesn't need an auth token, so we use fetch() directly
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.message);
        }
        showNotification(result.message);
        showLoginForm();
    } catch (error) {
        showNotification(error.message, 'error');
        console.error(error);
    }
}

/**
 * This is the fixed login function.
 * It correctly sets the global 'authToken' variable
 * *before* calling initializeApp(). This fixes the 422 errors.
 */
async function login() {
    const data = {
        email: document.getElementById('loginEmail').value,
        password: document.getElementById('loginPassword').value
    };

    try {
        // Login also doesn't need a token
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.message);
        }
        
        // --- THIS IS THE CRITICAL FIX ---
        authToken = result.access_token; // <-- Sets the global variable
        currentUser = result.user;
        localStorage.setItem('authToken', authToken); // <-- Sets for next visit
        localStorage.setItem('currentUser', JSON.stringify(currentUser));
        // --- END CRITICAL FIX ---
        
        showNotification(result.message);
        initializeApp(); // Now initializeApp() can call apiRequest() successfully
    } catch (error) {
        showNotification(error.message, 'error');
        console.error(error);
    }
}

async function logout() {
    try {
        await apiRequest('/logout', 'POST');
    } catch (error) {
        console.error("Logout failed, clearing session anyway");
    } finally {
        // Always log out the user on the frontend
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        if (socket) socket.disconnect();
        location.reload();
    }
}

function initializeApp() {
    document.getElementById('authContainer').style.display = 'none';
    document.getElementById('mainApp').style.display = 'block';
    
    document.getElementById('sidebarName').textContent = `${currentUser.first_name} ${currentUser.last_name}`;
    document.getElementById('sidebarAvatar').src = currentUser.profile_picture || 'https://via.placeholder.com/40';
    document.getElementById('createPostAvatar').src = currentUser.profile_picture || 'https://via.placeholder.com/40';
    
    connectSocket();
    loadFeed();
    loadStories();
    loadFriendRequests();
    loadOnlineFriends();
    loadNotifications();
}

function connectSocket() {
    if (socket.connected) {
        socket.emit('join', { user_id: currentUser.id });
        return;
    }
    
    // Re-initialize socket if it's disconnected
    socket = io(); 
    
    socket.on('connect', () => {
        console.log('Socket connected, joining room...');
        socket.emit('join', { user_id: currentUser.id });
    });
    
    socket.on('new_notification', (data) => {
        showNotification(data.content);
        loadNotifications();
    });
    
    socket.on('new_message', (data) => {
        showNotification(`New message from ${data.sender.first_name}`);
        updateMessageBadge();
    });

    socket.on('disconnect', (reason) => {
        console.log('Socket disconnected:', reason);
    });

    socket.on('connect_error', (err) => {
        console.error('Socket connection error:', err);
    });
}

async function loadFeed(page = 1) {
    try {
        const data = await apiRequest(`/feed?page=${page}&per_page=10`);
        const container = document.getElementById('postsContainer');
        
        if (page === 1) {
            container.innerHTML = '';
        }
        
        if (data.posts.length === 0 && page === 1) {
            container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><div>No posts yet. Start following people to see their posts!</div></div>';
            return;
        }
        
        data.posts.forEach(post => {
            container.innerHTML += createPostHTML(post);
        });
    } catch (error) {
        console.error("Failed to load feed:", error);
    }
}

function createPostHTML(post) {
    const reactions = post.reactions;
    const topReactions = Object.entries(reactions).filter(([k, v]) => v > 0).sort((a, b) => b[1] - a[1]).slice(0, 3);
    const reactionIcons = {
        like: '👍',
        love: '❤',
        haha: '😂',
        wow: '😮',
        sad: '😢',
        angry: '😠'
    };
    
    return `
        <div class="post" data-post-id="${post.id}">
            <div class="post-header">
                <img src="${post.author.profile_picture || 'https://via.placeholder.com/40'}" alt="${post.author.first_name}" class="post-avatar">
                <div class="post-author-info">
                    <div class="post-author-name">
                        ${post.author.first_name} ${post.author.last_name}
                        ${post.author.is_verified ? '✓' : ''}
                        ${post.feeling ? ` is feeling ${post.feeling}` : ''}
                        ${post.location ? ` at ${post.location}` : ''}
                    </div>
                    <div class="post-time">${formatTime(post.created_at)}</div>
                </div>
            </div>
            <div class="post-content">${post.content}</div>
            ${post.images && post.images.length > 0 ? `<img src="${post.images[0]}" alt="Post image" class="post-image">` : ''}
            <div class="post-stats">
                <div class="reactions-summary">
                    ${topReactions.map(([type, count]) => `<span class="reaction-icon">${reactionIcons[type]}</span>`).join('')}
                    <span>${post.likes_count > 0 ? post.likes_count : ''}</span>
                </div>
                <div>
                    <span>${post.comments_count} comments</span>
                    <span style="margin-left: 15px;">${post.shares_count} shares</span>
                </div>
            </div>
            <div class="post-interactions">
                <button class="interaction-btn ${post.user_liked ? 'active' : ''}" onclick="reactToPost(${post.id}, 'like')" onmouseenter="showReactionPicker(${post.id})" onmouseleave="hideReactionPicker(${post.id})">
                    ${post.user_reaction ? reactionIcons[post.user_reaction] : '👍'} ${post.user_reaction || 'Like'}
                    <div class="reaction-picker" id="reactionPicker${post.id}">
                        ${Object.entries(reactionIcons).map(([type, icon]) => 
                            `<span class="reaction-option" onclick="reactToPost(${post.id}, '${type}'); event.stopPropagation();">${icon}</span>`
                        ).join('')}
                    </div>
                </button>
                <button class="interaction-btn" onclick="toggleComments(${post.id})">💬 Comment</button>
                <button class="interaction-btn" onclick="sharePost(${post.id})">🔄 Share</button>
                <button class="interaction-btn" onclick="savePost(${post.id})">🔖 Save</button>
            </div>
            <div class="comments-section" id="comments${post.id}" style="display: none;">
                <div id="commentsList${post.id}"></div>
                <div class="comment-input-container">
                    <img src="${currentUser.profile_picture || 'https://via.placeholder.com/32'}" alt="You" class="comment-avatar">
                    <input type="text" class="comment-input" placeholder="Write a comment..." id="commentInput${post.id}" onkeypress="if(event.key==='Enter') addComment(${post.id})">
                </div>
            </div>
        </div>
    `;
}

function showReactionPicker(postId) {
    const picker = document.getElementById(`reactionPicker${postId}`);
    if (picker) picker.classList.add('active');
}

function hideReactionPicker(postId) {
    const picker = document.getElementById(`reactionPicker${postId}`);
    if (picker) picker.classList.remove('active');
}

async function reactToPost(postId, reactionType) {
    try {
        await apiRequest(`/posts/${postId}/react`, 'POST', { reaction_type: reactionType });
        loadFeed(); // Reload feed to show new reaction
    } catch (error) {
        console.error(error);
    }
}

async function toggleComments(postId) {
    const commentsSection = document.getElementById(`comments${postId}`);
    const commentsList = document.getElementById(`commentsList${postId}`);
    
    if (commentsSection.style.display === 'none') {
        commentsSection.style.display = 'block';
        commentsList.innerHTML = '<div class="loader"></div>'; // Show loader
        
        try {
            const data = await apiRequest(`/posts/${postId}`);
            commentsList.innerHTML = ''; // Clear loader
            data.comments.forEach(comment => {
                commentsList.innerHTML += createCommentHTML(comment);
            });
        } catch (error) {
            commentsList.innerHTML = 'Failed to load comments.';
            console.error(error);
        }
    } else {
        commentsSection.style.display = 'none';
    }
}

function createCommentHTML(comment) {
    return `
        <div class="comment">
            <img src="${comment.author.profile_picture || 'https://via.placeholder.com/32'}" alt="${comment.author.first_name}" class="comment-avatar">
            <div>
                <div class="comment-content">
                    <div class="comment-author">${comment.author.first_name} ${comment.author.last_name}</div>
                    <div class="comment-text">${comment.content}</div>
                </div>
                <div class="comment-actions">
                    <span class="comment-action" onclick="likeComment(${comment.id})">Like</span>
                    <span class="comment-action">Reply</span>
                    <span>${formatTime(comment.created_at)}</span>
                </div>
            </div>
        </div>
    `;
}

async function addComment(postId) {
    const input = document.getElementById(`commentInput${postId}`);
    const content = input.value.trim();
    
    if (!content) return;
    
    try {
        await apiRequest(`/posts/${postId}/comments`, 'POST', { content });
        input.value = '';
        // Re-load comments
        toggleComments(postId); // Close it
        toggleComments(postId); // Open it again to refresh
    } catch (error) {
        console.error(error);
    }
}

async function likeComment(commentId) {
    try {
        await apiRequest(`/comments/${commentId}/like`, 'POST');
        showNotification('Comment liked!');
    } catch (error) {
        console.error(error);
    }
}

async function sharePost(postId) {
    const caption = prompt('Add a caption (optional):');
    if (caption === null) return; // User clicked cancel

    try {
        await apiRequest(`/posts/${postId}/share`, 'POST', { caption: caption || '' });
        showNotification('Post shared to your timeline!');
        loadFeed();
    } catch (error) {
        console.error(error);
    }
}

async function savePost(postId) {
    try {
        await apiRequest(`/posts/${postId}/save`, 'POST');
        showNotification('Post saved!');
    } catch (error) {
        console.error(error);
    }
}

function showCreatePost() {
    document.getElementById('createPostModal').classList.add('active');
}

async function createPost() {
    const content = document.getElementById('postContent').value.trim();
    const location = document.getElementById('postLocation').value.trim();
    const feeling = document.getElementById('postFeeling').value;
    const privacy = document.getElementById('postPrivacy').value;
    
    if (!content) {
        showNotification('Please write something!', 'error');
        return;
    }
    
    try {
        await apiRequest('/posts', 'POST', {
            content,
            location: location || null,
            feeling: feeling || null,
            privacy
        });
        
        document.getElementById('postContent').value = '';
        document.getElementById('postLocation').value = '';
        document.getElementById('postFeeling').value = '';
        closeModal('createPostModal');
        showNotification('Your post has been shared!');
        loadFeed();
    } catch (error) {
        console.error(error);
    }
}

async function loadStories() {
    try {
        const data = await apiRequest('/stories');
        const container = document.getElementById('storiesContainer');
        
        // Clear old stories, but keep the "Create Story" button
        container.innerHTML = `
            <div class="story" onclick="showCreateStory()">
                <img src="https://via.placeholder.com/110x190" alt="Create Story">
                <div class="story-name">➕ Create Story</div>
            </div>
        `;

        data.stories.forEach(storyGroup => {
            container.innerHTML += `
                <div class="story" onclick="viewStory(${storyGroup.stories[0].id})">
                    <img src="${storyGroup.stories[0].media_url || 'https://via.placeholder.com/110x190'}" alt="${storyGroup.user.first_name}">
                    <img src="${storyGroup.user.profile_picture || 'https://via.placeholder.com/40'}" alt="${storyGroup.user.first_name}" class="story-avatar">
                    <div class="story-name">${storyGroup.user.first_name}</div>
                </div>
            `;
        });
    } catch (error) {
        console.error("Failed to load stories:", error);
    }
}

function showCreateStory() {
    const text = prompt('Enter your story text:');
    if (text) {
        createStory(text);
    }
}

async function createStory(text) {
    try {
        await apiRequest('/stories', 'POST', {
            text,
            media_type: 'text',
            background_color: '#667eea'
        });
        showNotification('Story published!');
        loadStories(); // Refresh stories
    } catch (error) {
        console.error(error);
    }
}

async function viewStory(storyId) {
    try {
        await apiRequest(`/stories/${storyId}/view`, 'POST');
        showNotification('Story viewed (see server log)');
        // In a real app, you'd open a story viewer modal here
    } catch (error) {
        console.error(error);
    }
}

async function loadFriendRequests() {
    try {
        const data = await apiRequest('/friends/requests');
        const widget = document.getElementById('friendRequestsWidget');
        const badge = document.getElementById('friendRequestBadge');
        
        if (data.friend_requests.length === 0) {
            widget.innerHTML = '<div style="color: #65676b; text-align: center;">No new requests</div>';
            badge.style.display = 'none';
        } else {
            badge.style.display = 'flex';
            badge.textContent = data.friend_requests.length;
            widget.innerHTML = '';
            
            data.friend_requests.forEach(req => {
                widget.innerHTML += `
                    <div class="friend-request">
                        <img src="${req.user.profile_picture || 'https://via.placeholder.com/60'}" alt="${req.user.first_name}">
                        <div class="friend-request-info">
                            <div class="friend-name">${req.user.first_name} ${req.user.last_name}</div>
                            <div class="friend-request-actions">
                                <button class="btn btn-primary" onclick="acceptFriendRequest(${req.id})">Confirm</button>
                                <button class="btn btn-secondary" onclick="rejectFriendRequest(${req.id})">Delete</button>
                            </div>
                        </div>
                    </div>
                `;
            });
        }
    } catch (error) {
        console.error("Failed to load friend requests:", error);
    }
}

async function acceptFriendRequest(friendshipId) {
    try {
        await apiRequest(`/friends/accept/${friendshipId}`, 'PUT');
        showNotification('Friend request accepted!');
        loadFriendRequests();
        loadOnlineFriends();
    } catch (error) {
        console.error(error);
    }
}

async function rejectFriendRequest(friendshipId) {
    try {
        await apiRequest(`/friends/reject/${friendshipId}`, 'DELETE');
        showNotification('Friend request declined');
        loadFriendRequests();
    } catch (error) {
        console.error(error);
    }
}

async function loadOnlineFriends() {
    try {
        const data = await apiRequest('/friends');
        const widget = document.getElementById('onlineFriendsWidget');
        
        const onlineFriends = data.friends.filter(f => f.is_online);
        
        if (onlineFriends.length === 0) {
            widget.innerHTML = '<div style="color: #65676b; text-align: center;">No friends online</div>';
        } else {
            widget.innerHTML = '';
            onlineFriends.forEach(friend => {
                widget.innerHTML += `
                    <div class="online-friend" onclick="openChat(${friend.id})">
                        <div style="position: relative;">
                            <img src="${friend.profile_picture || 'https://via.placeholder.com/36'}" alt="${friend.first_name}">
                            <div class="online-status"></div>
                        </div>
                        <span>${friend.first_name} ${friend.last_name}</span>
                    </div>
                `;
            });
        }
    } catch (error) {
        console.error("Failed to load friends:", error);
    }
}

async function loadNotifications() {
    try {
        const data = await apiRequest('/notifications');
        const badge = document.getElementById('notificationBadge');
        const unread = data.notifications.filter(n => !n.is_read).length;
        
        if (unread > 0) {
            badge.style.display = 'flex';
            badge.textContent = unread;
        } else {
            badge.style.display = 'none';
        }
    } catch (error) {
        console.error("Failed to load notifications:", error);
    }
}

async function showNotifications() {
    const modal = document.getElementById('notificationsModal');
    const list = document.getElementById('notificationsList');
    document.querySelector('#notificationsModal .modal-title').textContent = 'Notifications';
    list.innerHTML = '<div class="loader"></div>';
    modal.classList.add('active');

    try {
        const data = await apiRequest('/notifications');
        
        if (data.notifications.length === 0) {
            list.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🔔</div><div>No notifications yet</div></div>';
        } else {
            list.innerHTML = '';
            data.notifications.forEach(notif => {
                list.innerHTML += `
                    <div class="friend-request" style="opacity: ${notif.is_read ? 0.6 : 1}; cursor: pointer;" onclick="markNotificationRead(${notif.id})">
                        <img src="${notif.sender ? notif.sender.profile_picture || 'https://via.placeholder.com/40' : 'https://via.placeholder.com/40'}" alt="Notification">
                        <div class="friend-request-info">
                            <div class="friend-name">${notif.sender ? notif.sender.first_name : 'System'}</div>
                            <div class="mutual-friends">${notif.content}</div>
                            <div style="font-size: 12px; color: #65676b;">${formatTime(notif.created_at)}</div>
                        </div>
                    </div>
                `;
            });
        }
    } catch (error) {
        list.innerHTML = 'Failed to load notifications.';
        console.error(error);
    }
}

async function markNotificationRead(notifId) {
    try {
        await apiRequest(`/notifications/${notifId}/read`, 'PUT');
        loadNotifications(); // Update badge count
        showNotifications(); // Refresh list
    } catch (error) {
        console.error(error);
    }
}

async function showMessages() {
    const modal = document.getElementById('notificationsModal');
    const list = document.getElementById('notificationsList');
    document.querySelector('#notificationsModal .modal-title').textContent = 'Messages';
    list.innerHTML = '<div class="loader"></div>';
    modal.classList.add('active');

    try {
        const data = await apiRequest('/conversations');
        
        if (data.conversations.length === 0) {
            list.innerHTML = '<div class="empty-state"><div class="empty-state-icon">💬</div><div>No messages yet</div></div>';
        } else {
            list.innerHTML = '';
            data.conversations.forEach(conv => {
                list.innerHTML += `
                    <div class="friend-request" style="cursor: pointer;" onclick="openChat(${conv.user.id})">
                        <div style="position: relative;">
                            <img src="${conv.user.profile_picture || 'https://via.placeholder.com/60'}" alt="${conv.user.first_name}">
                            ${conv.user.is_online ? '<div class="online-status"></div>' : ''}
                        </div>
                        <div class="friend-request-info">
                            <div class="friend-name">${conv.user.first_name} ${conv.user.last_name}</div>
                            <div class="mutual-friends">${conv.last_message.content}</div>
                            <div style="font-size: 12px; color: #65676b;">${formatTime(conv.last_message.created_at)}</div>
                            ${conv.unread_count > 0 ? `<span class="badge" style="position: static; margin-top: 5px;">${conv.unread_count}</span>` : ''}
                        </div>
                    </div>
                `;
            });
        }
    } catch (error) {
        list.innerHTML = 'Failed to load messages.';
        console.error(error);
    }
}

function openChat(userId) {
    closeModal('notificationsModal');
    alert(`Chat feature coming soon! User ID: ${userId}`);
}

async function showFriends() {
    const modal = document.getElementById('notificationsModal');
    const list = document.getElementById('notificationsList');
    document.querySelector('#notificationsModal .modal-title').textContent = 'Friends';
    list.innerHTML = '<div class="loader"></div>';
    modal.classList.add('active');

    try {
        const data = await apiRequest('/friends');
        
        if (data.friends.length === 0) {
            list.innerHTML = '<div class="empty-state"><div class="empty-state-icon">👥</div><div>No friends yet</div></div>';
        } else {
            list.innerHTML = '';
            data.friends.forEach(friend => {
                list.innerHTML += `
                    <div class="friend-request">
                        <img src="${friend.profile_picture || 'https://via.placeholder.com/60'}" alt="${friend.first_name}">
                        <div class="friend-request-info">
                            <div class="friend-name">${friend.first_name} ${friend.last_name}</div>
                            <div class="friend-request-actions">
                                <button class="btn btn-primary" onclick="openChat(${friend.id})">Message</button>
                                <button class="btn btn-secondary" onclick="unfriend(${friend.id})">Unfriend</button>
                            </div>
                        </div>
                    </div>
                `;
            });
        }
    } catch (error) {
        list.innerHTML = 'Failed to load friends.';
        console.error(error);
    }
}

async function unfriend(friendId) {
    if (!confirm('Are you sure you want to unfriend this person?')) return;
    
    try {
        await apiRequest(`/friends/unfriend/${friendId}`, 'DELETE');
        showNotification('Friend removed');
        showFriends(); // Refresh the modal
    } catch (error) {
        console.error(error);
    }
}

async function showSavedPosts() {
    const container = document.getElementById('postsContainer');
    container.innerHTML = '<div class="loader"></div>';
    
    try {
        const data = await apiRequest('/saved-posts');
        
        if (data.saved_posts.length === 0) {
            container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🔖</div><div>No saved posts yet</div></div>';
        } else {
            container.innerHTML = '<h2 style="margin-bottom: 20px;">Saved Posts</h2>';
            data.saved_posts.forEach(saved_item => {
                // The post object is nested inside the saved_item
                container.innerHTML += createPostHTML(saved_item); 
            });
        }
    } catch (error) {
        container.innerHTML = 'Failed to load saved posts.';
        console.error(error);
    }
}

async function showProfile() {
    try {
        const data = await apiRequest(`/profile/${currentUser.id}`);
        alert(`Profile:\n\nName: ${data.first_name} ${data.last_name}\nUsername: @${data.username}\nBio: ${data.bio || 'No bio yet'}\nFollowers: ${data.followers_count}\nFollowing: ${data.following_count}\nPosts: ${data.posts_count}`);
    } catch (error) {
        console.error(error);
    }
}

async function showFriendRequests() {
    const modal = document.getElementById('notificationsModal');
    const list = document.getElementById('notificationsList');
    document.querySelector('#notificationsModal .modal-title').textContent = 'Friend Requests';
    list.innerHTML = '<div class="loader"></div>';
    modal.classList.add('active');

    try {
        const data = await apiRequest('/friends/requests');
        
        if (data.friend_requests.length === 0) {
            list.innerHTML = '<div class="empty-state"><div class="empty-state-icon">👥</div><div>No friend requests</div></div>';
        } else {
            list.innerHTML = '';
            data.friend_requests.forEach(req => {
                list.innerHTML += `
                    <div class="friend-request">
                        <img src="${req.user.profile_picture || 'https://via.placeholder.com/60'}" alt="${req.user.first_name}">
                        <div class="friend-request-info">
                            <div class="friend-name">${req.user.first_name} ${req.user.last_name}</div>
                            <div class="mutual-friends">${formatTime(req.created_at)}</div>
                            <div class="friend-request-actions">
                                <button class="btn btn-primary" onclick="acceptFriendRequest(${req.id}); showFriendRequests();">Confirm</button>
                                <button class="btn btn-secondary" onclick="rejectFriendRequest(${req.id}); showFriendRequests();">Delete</button>
                            </div>
                        </div>
                    </div>
                `;
            });
        }
    } catch (error) {
        list.innerHTML = 'Failed to load friend requests.';
        console.error(error);
    }
}

async function search() {
    const query = document.getElementById('searchInput').value.trim();
    
    if (query.length < 2) {
        loadFeed(); // Go back to feed if query is cleared
        return;
    }
    
    const container = document.getElementById('postsContainer');
    container.innerHTML = '<div class="loader"></div>';

    try {
        const data = await apiRequest(`/search?q=${encodeURIComponent(query)}&type=all`);
        
        container.innerHTML = '<h2 style="margin-bottom: 20px;">Search Results</h2>';
        
        if (data.users && data.users.length > 0) {
            container.innerHTML += '<h3 style="margin: 20px 0 10px 0;">People</h3>';
            data.users.forEach(user => {
                container.innerHTML += `
                    <div class="post">
                        <div class="friend-request">
                            <img src="${user.profile_picture || 'https://via.placeholder.com/60'}" alt="${user.first_name}">
                            <div class="friend-request-info">
                                <div class="friend-name">${user.first_name} ${user.last_name} ${user.is_verified ? '✓' : ''}</div>
                                <div class="mutual-friends">@${user.username}</div>
                                <div class="friend-request-actions">
                                    <button class="btn btn-primary" onclick="sendFriendRequest(${user.id})">Add Friend</button>
                                    <button class="btn btn-secondary" onclick="followUser(${user.id})">Follow</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
        }
        
        if (data.posts && data.posts.length > 0) {
            container.innerHTML += '<h3 style="margin: 20px 0 10px 0;">Posts</h3>';
            data.posts.forEach(post => {
                container.innerHTML += createPostHTML(post);
            });
        }
        
        if ((!data.users || data.users.length === 0) && (!data.posts || data.posts.length === 0)) {
            container.innerHTML += '<div class="empty-state"><div class="empty-state-icon">🔍</div><div>No results found</div></div>';
        }
    } catch (error) {
        container.innerHTML = 'Search failed to load.';
        console.error(error);
    }
}

async function sendFriendRequest(userId) {
    try {
        await apiRequest('/friends/request', 'POST', { friend_id: userId });
        showNotification('Friend request sent!');
    } catch (error) {
        console.error(error);
    }
}

async function followUser(userId) {
    try {
        await apiRequest(`/follow/${userId}`, 'POST');
        showNotification('You are now following this user!');
    } catch (error) {
        console.error(error);
    }
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
    
    return date.toLocaleDateString();
}

function updateMessageBadge() {
    const badge = document.getElementById('messageBadge');
    badge.style.display = 'flex';
    badge.textContent = parseInt(badge.textContent || 0) + 1;
}

// This runs when the script first loads
if (authToken && currentUser.id) {
    // If we have a token in localStorage, start the app
    initializeApp();
} else {
    // Otherwise, make sure the auth screen is visible
    document.getElementById('authContainer').style.display = 'flex';
    document.getElementById('mainApp').style.display = 'none';
}

document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});
