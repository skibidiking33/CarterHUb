from flask import render_template, request, session, redirect, url_for, jsonify, flash, make_response
from flask_socketio import emit, join_room, leave_room
from werkzeug.security import check_password_hash, generate_password_hash
from app import app, db, socketio
from models import Category, Game, Admin, ChatUser, ChatMessage, FriendRequest, Friendship, ChatGroup, GroupMembership
from datetime import datetime
import json

@app.route('/')
def index():
    # Check if admin parameter is present in query string
    if request.args.get('admin') is not None:
        if 'admin_logged_in' in session:
            return redirect(url_for('admin_panel'))
        return render_template('admin_login.html')
    
    # Regular index page
    categories = Category.query.order_by(Category.created_at.desc()).all()
    return render_template('index.html', categories=categories)

@app.route('/admin')
def admin_check():
    # Check if admin parameter is present
    if request.args.get('admin') is not None:
        if 'admin_logged_in' in session:
            return redirect(url_for('admin_panel'))
        return render_template('admin_login.html')
    return redirect(url_for('index'))

@app.route('/admin_login', methods=['POST'])
def admin_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Please enter both username and password')
        return render_template('admin_login.html')
    
    admin = Admin.query.filter_by(username=username).first()
    
    if admin and check_password_hash(admin.password_hash, password):
        session['admin_logged_in'] = True
        session['admin_id'] = admin.id
        return redirect(url_for('admin_panel'))
    else:
        flash('Invalid credentials')
        return render_template('admin_login.html')

@app.route('/admin_panel')
def admin_panel():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_check'))
    
    categories = Category.query.all()
    games = Game.query.all()
    return render_template('admin.html', categories=categories, games=games)

@app.route('/admin/add_category', methods=['POST'])
def add_category():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_check'))
    
    title = request.form.get('title')
    description = request.form.get('description')
    game_url = request.form.get('game_url')
    is_chat = 'is_chat' in request.form
    
    category = Category(
        title=title,
        description=description,
        game_url=game_url,
        is_chat=is_chat
    )
    
    db.session.add(category)
    db.session.commit()
    
    flash('Category added successfully!')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_category/<int:category_id>')
def delete_category(category_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_check'))
    
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    
    flash('Category deleted successfully!')
    return redirect(url_for('admin_panel'))

@app.route('/admin/add_game', methods=['POST'])
def add_game():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_check'))
    
    title = request.form.get('title')
    description = request.form.get('description')
    game_url = request.form.get('game_url')
    category_id = request.form.get('category_id')
    
    if not all([title, description, game_url, category_id]):
        flash('All fields are required')
        return redirect(url_for('admin_panel'))
    
    game = Game(
        title=title,
        description=description,
        game_url=game_url,
        category_id=int(category_id)
    )
    
    db.session.add(game)
    db.session.commit()
    
    flash('Game added successfully!')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_game/<int:game_id>')
def delete_game(game_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_check'))
    
    game = Game.query.get_or_404(game_id)
    db.session.delete(game)
    db.session.commit()
    
    flash('Game deleted successfully!')
    return redirect(url_for('admin_panel'))

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    return redirect(url_for('index'))

@app.route('/category/<int:category_id>')
def category_view(category_id):
    category = Category.query.get_or_404(category_id)
    
    if category.is_chat:
        return redirect(url_for('chat_login'))
    
    games = Game.query.filter_by(category_id=category_id).all()
    return render_template('category.html', category=category, games=games)

@app.route('/game/<int:game_id>')
def game(game_id):
    game = Game.query.get_or_404(game_id)
    return render_template('game.html', game=game)

@app.route('/chat_login')
def chat_login():
    return render_template('chat_login.html')

@app.route('/chat_register', methods=['POST'])
def chat_register():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Please fill in all fields')
        return redirect(url_for('chat_login'))
    
    # Check if user already exists
    existing_user = ChatUser.query.filter_by(username=username).first()
    if existing_user:
        flash('Username already exists!')
        return redirect(url_for('chat_login'))
    
    # Create new user
    user = ChatUser(
        username=username,
        email=f"{username}@carterhub.local",  # Auto-generate email
        password_hash=generate_password_hash(password)
    )
    
    db.session.add(user)
    db.session.commit()
    
    session['chat_user_id'] = user.id
    session['chat_username'] = user.username
    
    return redirect(url_for('chat'))

@app.route('/chat_signin', methods=['POST'])
def chat_signin():
    username = request.form.get('username')
    password = request.form.get('password')
    remember_me = request.form.get('remember_me')
    
    if not username or not password:
        flash('Please enter both username and password')
        return redirect(url_for('chat_login'))
    
    user = ChatUser.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password_hash, password):
        session['chat_user_id'] = user.id
        session['chat_username'] = user.username
        
        # Update online status
        user.is_online = True
        db.session.commit()
        
        # Set persistent cookie if remember me is checked
        resp = make_response(redirect(url_for('chat')))
        if remember_me:
            resp.set_cookie('chat_user_id', str(user.id), max_age=30*24*60*60)  # 30 days
            resp.set_cookie('chat_username', user.username, max_age=30*24*60*60)
        
        return resp
    else:
        flash('Invalid credentials!')
        return redirect(url_for('chat_login'))

@app.route('/chat')
def chat():
    # Check for persistent login cookies if not in session
    if 'chat_user_id' not in session:
        chat_user_id = request.cookies.get('chat_user_id')
        chat_username = request.cookies.get('chat_username')
        
        if chat_user_id and chat_username:
            # Verify the user still exists and restore session
            user = ChatUser.query.get(int(chat_user_id))
            if user and user.username == chat_username:
                session['chat_user_id'] = user.id
                session['chat_username'] = user.username
                user.is_online = True
                db.session.commit()
            else:
                # Clear invalid cookies
                resp = make_response(redirect(url_for('chat_login')))
                resp.set_cookie('chat_user_id', '', expires=0)
                resp.set_cookie('chat_username', '', expires=0)
                return resp
        else:
            return redirect(url_for('chat_login'))
    
    user_id = session['chat_user_id']
    user = ChatUser.query.get(user_id)
    
    # Get friends
    friendships = db.session.query(Friendship).filter(
        (Friendship.user1_id == user_id) | (Friendship.user2_id == user_id)
    ).all()
    
    friends = []
    for friendship in friendships:
        friend = friendship.user2 if friendship.user1_id == user_id else friendship.user1
        friends.append(friend)
    
    # Get friend requests
    pending_requests = FriendRequest.query.filter_by(
        receiver_id=user_id, 
        status='pending'
    ).all()
    
    # Get user's groups
    user_groups = db.session.query(ChatGroup).join(GroupMembership).filter(
        GroupMembership.user_id == user_id
    ).all()
    
    return render_template('chat.html', 
                         user=user, 
                         friends=friends, 
                         pending_requests=pending_requests,
                         groups=user_groups)

@app.route('/chat_logout')
def chat_logout():
    if 'chat_user_id' in session:
        user = ChatUser.query.get(session['chat_user_id'])
        if user:
            user.is_online = False
            db.session.commit()
    
    session.pop('chat_user_id', None)
    session.pop('chat_username', None)
    return redirect(url_for('chat_login'))

@app.route('/search_users')
def search_users():
    if 'chat_user_id' not in session:
        return jsonify([])
    
    query = request.args.get('q', '')
    current_user_id = session['chat_user_id']
    
    if len(query) < 2:
        return jsonify([])
    
    users = ChatUser.query.filter(
        ChatUser.username.ilike(f'%{query}%'),
        ChatUser.id != current_user_id
    ).limit(10).all()
    
    results = []
    for user in users:
        # Check if already friends
        friendship = db.session.query(Friendship).filter(
            ((Friendship.user1_id == current_user_id) & (Friendship.user2_id == user.id)) |
            ((Friendship.user1_id == user.id) & (Friendship.user2_id == current_user_id))
        ).first()
        
        # Check if friend request exists
        friend_request = FriendRequest.query.filter(
            ((FriendRequest.sender_id == current_user_id) & (FriendRequest.receiver_id == user.id)) |
            ((FriendRequest.sender_id == user.id) & (FriendRequest.receiver_id == current_user_id))
        ).first()
        
        results.append({
            'id': user.id,
            'username': user.username,
            'is_friend': friendship is not None,
            'has_pending_request': friend_request is not None and friend_request.status == 'pending'
        })
    
    return jsonify(results)

@app.route('/send_friend_request/<int:user_id>', methods=['POST'])
def send_friend_request(user_id):
    if 'chat_user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    sender_id = session['chat_user_id']
    
    # Check if request already exists
    existing_request = FriendRequest.query.filter(
        ((FriendRequest.sender_id == sender_id) & (FriendRequest.receiver_id == user_id)) |
        ((FriendRequest.sender_id == user_id) & (FriendRequest.receiver_id == sender_id))
    ).first()
    
    if existing_request:
        return jsonify({'error': 'Friend request already exists'}), 400
    
    friend_request = FriendRequest(
        sender_id=sender_id,
        receiver_id=user_id
    )
    
    db.session.add(friend_request)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/respond_friend_request/<int:request_id>/<action>')
def respond_friend_request(request_id, action):
    if 'chat_user_id' not in session:
        return redirect(url_for('chat_login'))
    
    friend_request = FriendRequest.query.get_or_404(request_id)
    
    if friend_request.receiver_id != session['chat_user_id']:
        flash('Unauthorized action!')
        return redirect(url_for('chat'))
    
    if action == 'accept':
        friend_request.status = 'accepted'
        
        # Create friendship
        friendship = Friendship(
            user1_id=friend_request.sender_id,
            user2_id=friend_request.receiver_id
        )
        db.session.add(friendship)
        
    elif action == 'reject':
        friend_request.status = 'rejected'
    
    db.session.commit()
    return redirect(url_for('chat'))

@app.route('/create_group', methods=['POST'])
def create_group():
    if 'chat_user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not name:
        return jsonify({'error': 'Group name is required'}), 400
    
    # Check if group name already exists
    existing_group = ChatGroup.query.filter_by(name=name).first()
    if existing_group:
        return jsonify({'error': 'Group name already exists'}), 400
    
    # Create the group
    group = ChatGroup(
        name=name,
        description=description,
        created_by=session['chat_user_id']
    )
    db.session.add(group)
    db.session.flush()  # Get the group ID
    
    # Add creator as member
    membership = GroupMembership(
        group_id=group.id,
        user_id=session['chat_user_id']
    )
    db.session.add(membership)
    db.session.commit()
    
    return jsonify({'success': True, 'group_id': group.id})

@app.route('/get_friends')
def get_friends():
    if 'chat_user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['chat_user_id']
    
    # Get friends
    friendships = db.session.query(Friendship).filter(
        (Friendship.user1_id == user_id) | (Friendship.user2_id == user_id)
    ).all()
    
    friends = []
    for friendship in friendships:
        friend = friendship.user2 if friendship.user1_id == user_id else friendship.user1
        friends.append({
            'id': friend.id,
            'username': friend.username,
            'is_online': friend.is_online
        })
    
    return jsonify({'friends': friends})

@app.route('/send_group_invite', methods=['POST'])
def send_group_invite():
    if 'chat_user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    group_id = data.get('group_id')
    friend_id = data.get('friend_id')
    
    if not group_id or not friend_id:
        return jsonify({'error': 'Group ID and friend ID are required'}), 400
    
    sender_id = session['chat_user_id']
    sender = ChatUser.query.get(sender_id)
    friend = ChatUser.query.get(friend_id)
    group = ChatGroup.query.get(group_id)
    
    if not group or not friend:
        return jsonify({'error': 'Group or friend not found'}), 404
    
    # Check if user is a member of the group
    membership = GroupMembership.query.filter_by(group_id=group_id, user_id=sender_id).first()
    if not membership:
        return jsonify({'error': 'You are not a member of this group'}), 403
    
    # Check if friend is already a member
    existing_membership = GroupMembership.query.filter_by(group_id=group_id, user_id=friend_id).first()
    if existing_membership:
        return jsonify({'error': 'User is already a member of this group'}), 400
    
    # Send invitation message to friend's DM
    invite_message = f"🎮 {sender.username} invited you to join the group '{group.name}'! Type '/accept {group.id}' to join or '/decline {group.id}' to decline."
    
    message = ChatMessage(
        content=invite_message,
        sender_id=sender_id,
        receiver_id=friend_id
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Group invitation sent to {friend.username}!'})

@app.route('/handle_group_command', methods=['POST'])
def handle_group_command():
    if 'chat_user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    command = data.get('command', '').strip()
    
    if not command.startswith('/'):
        return jsonify({'error': 'Invalid command'}), 400
    
    parts = command.split()
    action = parts[0][1:]  # Remove the '/' prefix
    
    user_id = session['chat_user_id']
    
    if action == 'accept' and len(parts) >= 2:
        try:
            group_id = int(parts[1])
            group = ChatGroup.query.get(group_id)
            
            if not group:
                return jsonify({'error': 'Group not found'}), 404
            
            # Check if already a member
            existing_membership = GroupMembership.query.filter_by(group_id=group_id, user_id=user_id).first()
            if existing_membership:
                return jsonify({'error': 'You are already a member of this group'}), 400
            
            # Add user to group
            membership = GroupMembership(
                group_id=group_id,
                user_id=user_id
            )
            db.session.add(membership)
            db.session.commit()
            
            return jsonify({'success': True, 'message': f'Successfully joined the group "{group.name}"!'})
            
        except ValueError:
            return jsonify({'error': 'Invalid group ID'}), 400
    
    elif action == 'decline' and len(parts) >= 2:
        try:
            group_id = int(parts[1])
            group = ChatGroup.query.get(group_id)
            
            if not group:
                return jsonify({'error': 'Group not found'}), 404
            
            return jsonify({'success': True, 'message': f'Declined invitation to join "{group.name}".'})
            
        except ValueError:
            return jsonify({'error': 'Invalid group ID'}), 400
    
    else:
        return jsonify({'error': 'Unknown command'}), 400

# Socket.IO events for real-time chat
@socketio.on('connect')
def on_connect():
    if 'chat_user_id' in session:
        join_room(f"user_{session['chat_user_id']}")
        emit('status', {'msg': f"{session['chat_username']} has connected"})

@socketio.on('disconnect')
def on_disconnect():
    if 'chat_user_id' in session:
        leave_room(f"user_{session['chat_user_id']}")

@socketio.on('send_message')
def handle_message(data):
    if 'chat_user_id' not in session:
        return
    
    sender_id = session['chat_user_id']
    receiver_id = data.get('receiver_id')
    group_id = data.get('group_id')
    content = data.get('content')
    
    if not content.strip():
        return
    
    # Save message to database
    message = ChatMessage(
        content=content,
        sender_id=sender_id,
        receiver_id=receiver_id,
        group_id=group_id
    )
    
    db.session.add(message)
    db.session.commit()
    
    # Prepare message data
    message_data = {
        'id': message.id,
        'content': content,
        'sender_username': session['chat_username'],
        'timestamp': message.timestamp.strftime('%H:%M')
    }
    
    if receiver_id:
        # Private message
        emit('new_message', message_data, room=f"user_{receiver_id}")
        emit('new_message', message_data, room=f"user_{sender_id}")
    elif group_id:
        # Group message
        group = ChatGroup.query.get(group_id)
        if group:
            for member in group.members:
                emit('new_message', message_data, room=f"user_{member.user_id}")

@socketio.on('get_messages')
def handle_get_messages(data):
    if 'chat_user_id' not in session:
        return
    
    user_id = session['chat_user_id']
    chat_with = data.get('chat_with')
    group_id = data.get('group_id')
    
    if chat_with:
        # Get private messages
        messages = ChatMessage.query.filter(
            ((ChatMessage.sender_id == user_id) & (ChatMessage.receiver_id == chat_with)) |
            ((ChatMessage.sender_id == chat_with) & (ChatMessage.receiver_id == user_id))
        ).order_by(ChatMessage.timestamp.asc()).limit(50).all()
    elif group_id:
        # Get group messages
        messages = ChatMessage.query.filter_by(group_id=group_id).order_by(
            ChatMessage.timestamp.asc()
        ).limit(50).all()
    else:
        return
    
    message_list = []
    for msg in messages:
        message_list.append({
            'id': msg.id,
            'content': msg.content,
            'sender_username': msg.sender.username,
            'is_own': msg.sender_id == user_id,
            'timestamp': msg.timestamp.strftime('%H:%M')
        })
    
    emit('messages_history', {'messages': message_list})
