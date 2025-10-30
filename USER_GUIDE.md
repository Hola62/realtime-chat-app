# User Guide - Realtime Chat App

## 🚀 Getting Started

### 1. Create Your Account

1. Go to http://localhost:8000/register.html
2. Fill in your details:
   - **First Name** (required)
   - **Last Name** (required)
   - **Email** (required, must be unique)
   - **Password** (min 8 characters, must have uppercase, lowercase, and number)
3. Click "Create Account"
4. You'll be automatically logged in and redirected to the chat page

### 2. Log In

1. Go to http://localhost:8000/login.html
2. Enter your email and password
3. Click "Sign In"
4. You'll be redirected to the chat page

---

## 👤 Managing Your Profile

### Access Your Profile

From the chat page, click the **"👤 Profile"** button in the top-right corner of the sidebar.

### Update Your Name

1. Click the "👤 Profile" button
2. Edit your **First Name** and **Last Name**
3. Click "Update Profile"
4. Your name will be updated across the entire app

### Upload/Update Profile Picture (DP)

1. Click the "👤 Profile" button
2. Scroll down to the "Profile Picture" section
3. Click "📁 Choose image file"
4. Select an image from your computer:
   - **Supported formats**: PNG, JPG, JPEG, GIF, WebP
   - **Maximum size**: 5MB
5. You'll see a preview of your image
6. Click "Upload Avatar"
7. Your profile picture is now saved!

### Return to Chat

Click the "Back to Chat" button at the bottom of the profile page.

---

## 💬 Using Chat Rooms

### Create a New Room

1. Click the **"+ New"** button in the sidebar
2. Enter a room name
3. Click "Create Room"
4. The room will be created and automatically selected
5. You can now start chatting!

### Join a Room

Simply click on any room in the sidebar to join it and start chatting.

### Delete a Room You Created

**Important**: You can only delete rooms that YOU created.

1. Look for the **"🗑️ Delete"** button next to rooms you created
2. Click the delete button
3. Confirm the deletion in the popup dialog
4. **Warning**: This will delete ALL messages in the room permanently!

The delete button only appears on rooms you created, so you won't see it on rooms created by other users.

---

## 📨 Sending Messages

### Send a Message

1. Select a room from the sidebar
2. Type your message in the input box at the bottom
3. Press **Enter** or click the **Send** button
4. Your message will appear instantly for all users in the room

### View Message History

When you join a room, the last 50 messages are automatically loaded and displayed.

### Typing Indicator

When you type a message, other users in the room will see a "User is typing..." indicator in real-time.

---

## 🟢 Online/Offline Status

Your status is automatically managed:

- **Online**: When you're connected to the chat
- **Offline**: When you close the browser or disconnect

Other users can see when you come online or go offline (status changes are broadcast in real-time).

---

## 🎨 Features Overview

### ✅ What You Can Do

| Feature              | How to Use                                |
| -------------------- | ----------------------------------------- |
| **Register**         | Create account with email and password    |
| **Login**            | Sign in with your credentials             |
| **Update Profile**   | Click "👤 Profile" → Edit name → Save     |
| **Upload Avatar**    | Click "👤 Profile" → Choose file → Upload |
| **Create Room**      | Click "+ New" → Enter name → Create       |
| **Delete Room**      | Click "🗑️ Delete" (only on your rooms)    |
| **Send Messages**    | Select room → Type → Send                 |
| **View History**     | Join any room to see past messages        |
| **Typing Indicator** | Start typing to show others you're active |
| **Online Status**    | Automatically shown when connected        |
| **Logout**           | Click "Logout" button in sidebar          |

---

## 📱 Quick Tips

### Profile Management

- ✅ **DO**: Upload clear, appropriate profile pictures
- ✅ **DO**: Keep your name up to date
- ℹ️ **TIP**: Your avatar appears next to your messages (feature coming soon!)

### Room Management

- ✅ **DO**: Create rooms with descriptive names
- ✅ **DO**: Delete rooms you no longer need
- ⚠️ **CAREFUL**: Deleting a room deletes ALL its messages permanently
- ℹ️ **TIP**: Only you can delete rooms you created

### Messaging

- ✅ **DO**: Be respectful and friendly
- ✅ **DO**: Use the typing indicator to show you're responding
- ℹ️ **TIP**: Messages are stored forever (until the room is deleted)

---

## 🔐 Security & Privacy

- ✅ Passwords are securely hashed
- ✅ All API requests require authentication (JWT tokens)
- ✅ You can only delete your own rooms
- ✅ Profile pictures are validated for size and type
- ✅ Your email is never shown to other users (only name is visible)

---

## 🆘 Troubleshooting

### "Redirecting to login after registration"

- **Solution**: Make sure both frontend (port 8000) and backend (port 5000) servers are running
- Check browser console (F12) for error messages

### "Cannot upload profile picture"

- **Check**: File size is under 5MB
- **Check**: File format is PNG, JPG, JPEG, GIF, or WebP
- **Try**: A different image or reduce the file size

### "Cannot delete room"

- **Check**: You created this room (delete button only appears on your rooms)
- **Check**: You're logged in with the correct account

### "Messages not appearing"

- **Check**: You're connected (look for "Connected" status)
- **Try**: Refresh the page
- **Check**: Browser console for errors

---

## 📞 Features Coming Soon

- [ ] User avatars shown in messages
- [ ] Online/offline indicators in user list
- [ ] Read receipts
- [ ] File sharing
- [ ] Direct messages (1-on-1 chat)
- [ ] Message search
- [ ] Emoji picker
- [ ] Voice messages

---

## 🎯 Summary

You now have a fully functional real-time chat application with:

- ✅ Secure user accounts
- ✅ Profile management with avatar upload
- ✅ Real-time messaging
- ✅ Room creation and deletion
- ✅ Message history
- ✅ Typing indicators
- ✅ Online/offline presence

**Enjoy chatting!** 💬
