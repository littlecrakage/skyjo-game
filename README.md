# Skyjo Game - TODO List

## ✅ Completed Features

### Core Game
- [x] Project structure (Flask, SocketIO, SQLAlchemy)
- [x] Database models (Game, Player)
- [x] Skyjo deck (150 cards: -2 to 12)
- [x] Card dealing (12 cards per player, 4x3 grid)
- [x] Initial 2-card reveal phase
- [x] Starting player rule (highest revealed total)
- [x] Draw from deck or discard pile
- [x] Place card or discard & reveal
- [x] Turn-based gameplay via WebSockets
- [x] Column elimination (3 matching cards)
- [x] Round end when player reveals all cards
- [x] Scoring with penalty rule (doubled if trigger player isn't lowest)
- [x] Game end at 100+ points
- [x] Winner announcement with final rankings

### Multiplayer
- [x] Room creation with 6-character codes
- [x] Join game by code
- [x] Public/private lobbies
- [x] Public lobbies list with auto-refresh
- [x] 2-8 players support
- [x] Spectator mode
- [x] Real-time updates via WebSockets

### Bots
- [x] Add bot with difficulty popup
- [x] Easy bot (random choices)
- [x] Medium bot (smart decisions)
- [x] Hard bot (card counting AI)
- [x] Bots auto-reveal initial cards

### UI/UX
- [x] Minimalist clean design
- [x] Card color coding by value
- [x] Matching column highlight
- [x] Turn indicator
- [x] Timer display
- [x] Round end overlay with scores
- [x] Game end screen with winner
- [x] Language switcher (English/French)
- [x] Fixed layout (no jumping when holding card)

---

## 🔄 In Progress

<!-- *(nothing currently)* -->

---

## 📋 TODO - Priority

### High Priority
- [x] **Timer enforcement** - Auto-skip turn when timer runs out (auto-draw + place on random card)
- [x] **Disconnection handling** - Handle player disconnect gracefully
- [x] **Navbar/menu**  to abandon game, back on the home page, link to the github
- [x] **Deployment to Hetzner** - Get the game online
- [x] **Delete Deserted Game** - Game that are empty of non-bot player should be deleted

### Medium Priority
- [x] Kick/remove player option for host
- [ ] Reconnection support (rejoin with session)
- [ ] Mobile responsive layout improvements

### Low Priority / Nice-to-Have
- [x] Make it easy to spot when not playing by greying out the board
- [ ] Sound effects (card flip, turn notification)
- [ ] Card flip animations
- [x] Rematch button after game ends
- [ ] Spectator count display
- [ ] Game history / statistics
- [ ] Player avatars
- [ ] Chat system (optional)
- [x] Add Tipping system like Ko-fi

---

## 🐛 Known Bugs

*(none currently reported)*

---

## 📝 Notes

- Using SQLite for development, PostgreSQL-ready for production
- ES5 JavaScript (no arrow functions) to avoid Jinja2 conflicts
- Translations in `/static/js/translations.js`

---

*Last updated: Feb 17, 2026*
# Test PR workflow
