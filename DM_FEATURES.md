# Direct Messages - New Features

## What's New

### 1. Persistent DM List

- Direct Messages now appear in a dedicated sidebar section
- Users you've messaged stay in your list for quick access
- List persists across sessions (stored in localStorage)
- Click any DM to jump back into that conversation

### 2. Server-Side DM Persistence

- All private messages are now saved to the database
- Message history loads when you open a DM
- New table: `private_messages` with:
  - room_key (e.g., "private_1_2")
  - sender_id, receiver_id
  - content, timestamp, deleted flag

### 3. Unread Message Counts

- Blue badge shows number of unread messages per DM
- Counter increments when receiving messages while:
  - Not viewing that DM
  - In another chat or room
- Counter resets to 0 when you open the DM

### 4. Last Message Preview

- Each DM shows a snippet of the most recent message
- Preview updates automatically when:
  - You send a message
  - You receive a message
- Truncated to 50 characters with ellipsis

### 5. Relative Timestamps

- Shows when the last message was sent:
  - "now" - less than a minute ago
  - "5m" - minutes ago
  - "2h" - hours ago
  - "3d" - days ago
  - "Nov 1" - older than a week

## How to Use

### Starting a DM

1. Use the search bar at the top of the sidebar
2. Type a user's name
3. Click "Message" button next to their name
4. The DM opens and they're added to your DM list

### Viewing DM History

- Click on any user in the "Direct Messages" section
- Their complete message history loads automatically
- Scroll up to see older messages

### Tracking Unread Messages

- The blue badge next to a DM shows unread count
- Opens DM to mark messages as read
- Badge disappears when count reaches 0

## Technical Details

### Frontend Changes

- **chat.html**: Added styles for DM list, badges, previews, timestamps
- **chat.js**:
  - New state: `dmMetadata` (localStorage-backed)
  - Functions: `loadDMMetadata`, `saveDMMetadata`, `updateDMMetadata`, `clearUnreadForDM`, `formatRelativeTime`
  - Enhanced `renderRecentDMs` to show preview, time, unread badge
  - Updates metadata on send and receive

### Backend Changes

- **models/private_message_model.py**: New file
  - `init_private_messages_table()`
  - `create_private_message(room_key, sender_id, receiver_id, content)`
  - `get_private_messages(room_key, limit=50)`
- **sockets/chat_events.py**: Updated handlers
  - `send_private_message`: Saves to DB, emits with ID and timestamp
  - `get_private_messages`: Fetches from DB instead of returning empty list

### Data Storage

#### localStorage Keys

- `recent_dms`: Array of user objects (id, first_name, last_name, avatar_url)
- `dm_metadata`: Object mapping user_id -> { unread, lastMessage, lastTime }

#### Database Table

```sql
CREATE TABLE private_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_key VARCHAR(64) NOT NULL,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    content TEXT NOT NULL,
    deleted BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- indexes and foreign keys
)
```

## Example Flow

1. **User searches for "chat tester"**
   - Search results appear below search bar
2. **User clicks "Message"**
   - DM view opens
   - "chat tester" added to DM list
   - Metadata initialized: { unread: 0, lastMessage: '', lastTime: null }
3. **User sends "Hello!"**
   - Message saves to DB
   - Metadata updates: { unread: 0, lastMessage: 'Hello!', lastTime: '2025-11-01T...' }
   - DM list shows: "Hello!" and "now"
4. **User switches to a room**
   - DM list still visible in sidebar
5. **"chat tester" replies "Hi there!"**
   - Message saves to DB
   - Metadata updates: { unread: 1, lastMessage: 'Hi there!', lastTime: '...' }
   - Blue badge appears with "1"
   - Preview updates to "Hi there!"
6. **User clicks on "chat tester" in DM list**
   - DM opens, history loads
   - Metadata updates: { unread: 0, ... }
   - Badge disappears

## Future Enhancements

Potential next features:

- Online/offline indicator dots in DM list
- Message delivery/read receipts
- DM deletion (similar to room messages)
- Edit sent DMs
- Pagination for very long DM histories
- Search within DMs
- Pin important DMs to top
- Mute/unmute DM notifications
- Group DMs (3+ participants)
