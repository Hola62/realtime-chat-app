# Quick Test Guide - DM Features

## ✅ What to Look For

### DM List Appearance

```text
┌─────────────────────────────────┐
│  DIRECT MESSAGES                │
├─────────────────────────────────┤
│  👤  John Doe              2    │ ← Unread badge (blue)
│      Hey, are you there?   5m   │ ← Last message + time
├─────────────────────────────────┤
│  👤  Chat Tester                │
│      Thanks!               1h   │
├─────────────────────────────────┤
│  👤  Jane Smith                 │
│      See you tomorrow!     2d   │
└─────────────────────────────────┘
```

## 🧪 Test Steps

### Test 1: Send First DM

1. Open chat app: <http://localhost:8000/chat.html>
2. Type "chat" in the user search bar
3. Click "Message" next to "Chat Tester"
4. **Expected**:
   - DM view opens
   - "Chat Tester" appears in DM list
   - Preview shows "No messages yet"

### Test 2: Send Message

1. Type "Hello!" in the message input
2. Press Send
3. **Expected**:
   - Message appears in chat
   - DM list updates:
     - Preview: "Hello!"
     - Time: "now"
     - No unread badge (you sent it)

### Test 3: Receive Message (Unread Count)

1. Open a second browser window (incognito mode)
2. Login as "Chat Tester"
3. In second window, search for your user and send "Hi there!"
4. Switch back to first window (but stay in a room, not the DM)
5. **Expected**:
   - Blue badge appears with "1"
   - Preview updates: "Hi there!"
   - Time updates: "now"

### Test 4: Clear Unread

1. Click on "Chat Tester" in the DM list
2. **Expected**:
   - DM opens
   - All messages visible
   - Badge disappears (unread = 0)

### Test 5: Multiple Unread

1. Have Chat Tester send 3 messages while you're in a room
2. **Expected**:
   - Badge shows "3"
   - Preview shows the most recent message
   - Time shows when the last message was sent

### Test 6: Persistence

1. Send/receive some DMs
2. Close the browser tab
3. Reopen <http://localhost:8000/chat.html>
4. **Expected**:
   - DM list still shows all conversations
   - Unread counts preserved
   - Last message previews preserved
   - Click a DM to load full history

## 🎨 Visual Elements

### Unread Badge

- **Color**: Blue (#3b82f6)
- **Shape**: Rounded pill
- **Position**: Right side of DM item
- **Content**: Number (e.g., "1", "5", "12")

### Last Message Preview

- **Color**: Light gray (#94a3b8)
- **Font size**: 12px
- **Max length**: 50 characters
- **Truncation**: Ellipsis (...)
- **Position**: Below user name

### Timestamp

- **Format**:
  - "now" (< 1 min)
  - "Xm" (minutes)
  - "Xh" (hours)
  - "Xd" (days)
  - "Nov 1" (> 1 week)
- **Color**: Dark gray (#64748b)
- **Font size**: 11px
- **Position**: Top right of DM item

## 🐛 Troubleshooting

### DM list doesn't update

- Check browser console for errors
- Verify backend is running (<http://localhost:5000/health>)
- Try refreshing the page

### Messages not persisting

- Check database connection (<http://localhost:5000/health/db>)
- Verify MySQL is running
- Check backend console for DB errors

### Unread count stuck

- Open developer tools → Application → Local Storage
- Find `dm_metadata` key
- Can manually edit or delete to reset

### Preview not showing

- Send a new message to refresh
- Check that `updateDMMetadata()` is being called
- Look for JS errors in console

## 📊 Data Verification

### Check localStorage

```javascript
// In browser console:
JSON.parse(localStorage.getItem("recent_dms"));
// Should show: [{id: X, first_name: "...", ...}, ...]

JSON.parse(localStorage.getItem("dm_metadata"));
// Should show: {"1": {unread: 0, lastMessage: "...", lastTime: "..."}, ...}
```

### Check Database

```sql
-- In MySQL:
SELECT * FROM private_messages ORDER BY timestamp DESC LIMIT 10;
-- Should show your sent/received DMs
```

## ✨ Success Criteria

- ✅ DM list persists across page refreshes
- ✅ Unread badges appear and increment correctly
- ✅ Unread badges clear when opening DM
- ✅ Last message preview updates on send/receive
- ✅ Timestamps show relative time (now, Xm, Xh, Xd)
- ✅ Clicking DM opens conversation with full history
- ✅ Messages persist in database
- ✅ Multiple DM conversations can be active
- ✅ Active DM is highlighted in list
