# Hay There — Horse Tinder 🐴

Swipe right on horses. Match. Chat (in neighs).

A plain static app (HTML/CSS/JS, no build step, no dependencies), same style as the rest of this repo.

- Swipe by dragging the card, the ✕ / ♥ / 🍬 buttons, or the ← → ↑ keys
- 🍬 (sugar cube) is the super-like: it always matches
- Right-swiping matches only horses that like you back (`likesYou` in `js/horses.js`)
- Matches open a chat with canned, in-character replies
- Swipes, matches and chats persist in `localStorage`; "Reset everything" clears them

Run it: open `index.html`, or `npx serve .` from this folder.

Add a horse by adding an object to the `HORSES` array in `js/horses.js`.
