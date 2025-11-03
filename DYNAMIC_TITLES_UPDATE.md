# Dynamic Page Titles Update

## Overview

Updated the browser tab title to dynamically show the current context instead of always showing "Chat - Realtime Chat App".

## Changes Made

### 1. Added Dynamic Title Function

**File:** `frontend/js/chat.js`

```javascript
// Update page title dynamically
function updatePageTitle(title) {
  if (title) {
    document.title = `${title} - Realtime Chat App`;
  } else {
    document.title = "Chat - Realtime Chat App";
  }
}
```

### 2. Updated Room Selection

When you join a room, the title now shows the room name:

- **Before:** `Chat - Realtime Chat App`
- **After:** `General - Realtime Chat App` (or whatever room you're in)

### 3. Updated Private Chat

When you're chatting with someone, the title shows their name:

- **Before:** `Chat - Realtime Chat App`
- **After:** `John Doe - Realtime Chat App`

## Browser Tab Behavior

| Page/Context         | Tab Title                            |
| -------------------- | ------------------------------------ |
| Login page           | `Login - Realtime Chat App`          |
| Register page        | `Register - Realtime Chat App`       |
| Reset password       | `Reset Password - Realtime Chat App` |
| Profile page         | `Profile - Realtime Chat App`        |
| Chat (no room)       | `Chat - Realtime Chat App`           |
| In room "General"    | `General - Realtime Chat App`        |
| DM with "Jane Smith" | `Jane Smith - Realtime Chat App`     |
| In room "Tech Talk"  | `Tech Talk - Realtime Chat App`      |

## User Benefits

1. **Easy Navigation** - When you have multiple tabs open, you can quickly identify which chat/room you're in
2. **Better Context** - The tab title tells you exactly what you're looking at
3. **Professional UX** - Matches behavior of WhatsApp Web, Slack, Discord, etc.

## Examples

### Scenario 1: Multiple Rooms Open

```text
Tab 1: General - Realtime Chat App
Tab 2: Tech Talk - Realtime Chat App
Tab 3: Random - Realtime Chat App
```

### Scenario 2: DM Conversations

```text
Tab 1: John Doe - Realtime Chat App
Tab 2: Jane Smith - Realtime Chat App
Tab 3: Profile - Realtime Chat App
```

### Scenario 3: Mixed

```text
Tab 1: General - Realtime Chat App (room)
Tab 2: Sarah Johnson - Realtime Chat App (DM)
Tab 3: Login - Realtime Chat App (login page)
```

## Technical Implementation

### When Joining a Room

```javascript
function selectRoom(roomId, roomName) {
  // ... existing code ...
  currentRoom = { id: roomId, name: roomName };
  updatePageTitle(roomName); // NEW: Update browser tab title
  // ... rest of code ...
}
```

### When Starting a Private Chat

```javascript
function startPrivateChat(user) {
  // ... existing code ...
  const userName = `${user.first_name} ${user.last_name}`;
  document.getElementById("currentRoomName").textContent = userName;
  updatePageTitle(userName); // NEW: Update browser tab title
  // ... rest of code ...
}
```

## Browser Compatibility

✅ Works on all modern browsers (Chrome, Firefox, Safari, Edge)
✅ No external dependencies
✅ Pure JavaScript `document.title` API

## Testing

1. **Test Room Switching:**

   - Open chat page
   - Click different rooms
   - Verify tab title changes to room name

2. **Test Private Messages:**

   - Search for a user
   - Start a DM
   - Verify tab title shows person's name

3. **Test Multiple Tabs:**
   - Open multiple chat tabs
   - Navigate to different rooms/DMs in each
   - Verify each tab shows correct context

## Future Enhancements

Possible additions:

- Show unread count in title: `(3) John Doe - Realtime Chat App`
- Blink/flash title on new message when tab not focused
- Show typing indicator in title: `John Doe is typing... - Realtime Chat App`
- Emoji indicators: `🔴 John Doe - Realtime Chat App` (for online/offline)

## Code Locations

- **Main function:** `frontend/js/chat.js` - `updatePageTitle()`
- **Room selection:** `frontend/js/chat.js` - `selectRoom()`
- **Private chat:** `frontend/js/chat.js` - `startPrivateChat()`
