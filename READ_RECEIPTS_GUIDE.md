# Read Receipts & Unread Counter - WhatsApp-Style

## New Features Added

### 1. **Unread Message Counter** ✅

- Shows the **exact number** of unread messages in the DM list
- Increments for **every message** received (not just once per conversation)
- Persists across page refreshes
- Clears when you open the DM

### 2. **Read Receipts (Checkmarks)** ✅

- Single checkmark (✓): Message sent but **not read**
- Double checkmark (✓✓): Message **read** by recipient
- Checkmarks appear next to the timestamp on your sent messages
- Updates in real-time when recipient opens your message

## How It Works

### Visual Indicators

**In DM List:**

```text
┌────────────────────────────────┐
│ 👤 John Doe                 3  │ ← Unread count badge
│     New message here!      2m  │
└────────────────────────────────┘
```

**In Chat View (Your Sent Messages):**

```text
You: Hello!                12:30 ✓   ← Sent, unread
You: How are you?          12:31 ✓✓  ← Sent and read
```

## Test Steps

### Test 1: Unread Counter

1. Open two browser windows (or one incognito)
2. Login as different users in each
3. From Window 1: Send 3 messages to User 2
4. In Window 2 (User 2): **Stay in a room or different chat**
5. **Expected**: User 1's DM shows badge with "3"
6. Click on User 1's DM
7. **Expected**: Badge disappears (messages marked as read)

### Test 2: Read Receipts

1. Window 1 (User 1): Send "Hello!" to User 2
2. **Expected**: Message shows single checkmark (✓)
3. Window 2 (User 2): Click on User 1's DM to open it
4. **Expected in Window 1**: Checkmark updates to double (✓✓)

### Test 3: Multiple Messages

1. Window 1: Send 5 messages quickly
2. **Expected**: All show single checkmark (✓)
3. Window 2: Open the DM
4. **Expected**: All checkmarks turn to double (✓✓) in Window 1

## Technical Implementation

### Database Changes

```sql
ALTER TABLE private_messages
ADD COLUMN read_status BOOLEAN DEFAULT FALSE;
```

### New Backend Functions

- `mark_messages_as_read(room_key, user_id)` - Marks all messages as read
- `get_unread_count(room_key, user_id)` - Returns count of unread messages

### Socket.IO Events

**New Server → Client Events:**

- `messages_read` - Emitted when someone reads your messages

  ```javascript
  {
    room_id: "private_1_2",
    reader_id: 2
  }
  ```

**Updated Events:**

- `private_message` - Now includes `read_status: false`
- `private_messages_history` - Now includes `read_status` for each message

### Frontend Changes

**New CSS Classes:**

- `.message-read-status` - Container for checkmarks
- `.message-read-status.read` - Blue/highlighted checkmarks

**New Functions:**

- `updateMessagesReadStatus(isRead)` - Updates all checkmarks in current chat

## Unread Count Logic

```javascript
// When receiving a message:
if (sender !== me && !currentlyViewingThisDM) {
  dmMetadata[senderId].unread += 1;  // Increment counter
}

// When opening a DM:
clearUnreadForDM(userId);  // Reset to 0
socket.emit('get_private_messages', ...);  // Also marks as read on server
```

## Read Receipt States

| Checkmark | Meaning        | Color      |
| --------- | -------------- | ---------- |
| ✓         | Sent, not read | Light gray |
| ✓✓        | Sent and read  | Blue/cyan  |

## Browser Compatibility

- Checkmark characters (✓) work on all modern browsers
- Fallback: Can use icons/SVG if needed
- Mobile: Touch-friendly, works on iOS/Android

## Privacy Notes

- Only **your sent messages** show read receipts
- Received messages **don't** show checkmarks
- Read receipts only work in **private chats** (not group rooms)

## Troubleshooting

### Unread count not incrementing

- Check browser console for Socket.IO errors
- Verify `updateDMMetadata()` is being called
- Check localStorage: `dm_metadata` should have `unread` field

### Checkmarks not updating

- Verify Socket.IO connection (`connected` event)
- Check `messages_read` event in console
- Ensure `read_status` field exists in database

### Counter doesn't clear

- Verify `clearUnreadForDM()` is called when opening DM
- Check `mark_messages_as_read()` backend function
- Look for DB errors in backend console

## Future Enhancements

Potential additions:

- Three-state checkmarks (sent → delivered → read)
- Timestamp when message was read
- "Last seen" indicator
- Typing indicators with read receipts
- Bulk mark as unread
- Notification sound for new messages
- Desktop notifications

## Code Locations

### Backend

- `backend/models/private_message_model.py` - DB functions
- `backend/sockets/chat_events.py` - Socket handlers

### Frontend

- `frontend/js/chat.js` - Logic and Socket.IO listeners
- `frontend/chat.html` - CSS for checkmarks

## Success Criteria

- ✅ Unread badge shows correct count (1, 2, 3, etc.)
- ✅ Badge increments for each new message
- ✅ Badge clears when DM is opened
- ✅ Single checkmark appears on sent messages
- ✅ Checkmark turns to double when recipient opens DM
- ✅ Works across multiple browser windows/tabs
- ✅ Persists across page refreshes
