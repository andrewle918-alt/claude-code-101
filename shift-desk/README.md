# Sweep

A quiet place to collect the week's coursework and keep it moving — built around
one habit: **when an Access One shift starts, go through Canvas first.**

Live at `https://<username>.github.io/claude-code-101/shift-desk/`

## What it does

- **Reminds you only on Access One shifts.** Shifts you mark `Access One` show a
  live banner at shift start telling you to sweep Canvas. Every other shift is
  displayed for context and never nags.
- **Walks you through Canvas.** The Sweep tab is a per-course checklist —
  Announcements, Assignments, this week's module, Grades — so nothing gets
  skipped. It resets every Monday.
- **Holds the tasks.** Add anything you find, tag it to a course, give it a due
  date and a rough effort. Today / Week / All views group it for you.
- **Keeps your data yours.** Everything lives in `localStorage` in your browser.
  No account, no server, nothing uploaded.

## Setting up your schedule

Your shifts are **not** in this repo, on purpose: a shift schedule says exactly
where a named person is every week, and this repo is public. `CONFIG.SHIFTS` in
`js/config.js` ships empty.

Load yours once, on your own device — **Settings → Schedule → Import schedule** —
by pasting a JSON list of shifts. It's validated on the way in, so a mistyped
paste tells you what's wrong instead of silently leaving you with no reminders.
From then on it lives in `localStorage` in that browser and goes nowhere else.

```json
[{"id":"example","day":4,"start":"09:00","end":"11:00","accessOne":true,
  "reminders":["09:00"],
  "segments":[{"start":"09:00","end":"10:00","role":"Access 1"},
              {"start":"10:00","end":"11:00","role":"Access 2"}]}]
```

| Field | Means |
|---|---|
| `day` | 0 = Sunday … 6 = Saturday |
| `start` / `end` | the whole block you're at the desk, `"HH:MM"` |
| `accessOne` | does this block contain any Access 1 hour? (a label) |
| `reminders` | the times it pings. Empty = never pings |
| `segments` | hour-by-hour roles, shown in the app for context |

**Copy mine out** in the same panel dumps your current shifts back as JSON — use
it to move your setup to another browser, or to keep a backup.

A block pings once per entry in `reminders`, so putting a single time there
covers a shift holding several Access 1 hours.

## Adding and removing reminders

Each shift carries its own list of reminder times, and nothing about it is fixed.
In **Settings → Shifts**, every shift shows its reminders as chips:

- **× on a chip** removes that reminder.
- **Add reminder** with a time adds another — a shift can carry as many as you
  like, so you can ping at both 12 and 2 if you decide you want that.
- **Strip a shift to no reminders** and it stays silent while still showing up
  in your week for context. That's how Tuesday is set.

A shift fires for exactly the reminders listed under it. `Access One` marks which
blocks contain Access 1 hours; it labels the shift but doesn't control firing.
The same list drives the browser notification and every alarm in the `.ics`
export. In code it's `CONFIG.SHIFTS[].reminders` in `js/config.js`.

## Where your reminders come from

Three independent layers, so nothing depends on the app being open:

1. **Google Calendar** — your five Access One events each carry an email
   reminder and a phone popup at the block's start. This is the one that reaches
   you when the app is closed, and it follows the November DST change on its own.
2. **The app** — the live banner, plus an optional browser notification while
   the tab is open.
3. **The .ics export** — Settings → Reminders, for loading the same alarms into
   any other calendar.

Editing reminders in the app changes layers 2 and 3. Layer 1 lives on your
Google Calendar and is edited there.

## Getting reminders when the tab is closed

The in-app banner and the browser notification only fire while the page is open.
For alerts that reach your phone, use **Settings → Reminders → Download calendar
file (.ics)**. It generates a weekly recurring event with an alarm for each
Access One shift; import it into Google Calendar, Apple Calendar, or Outlook and
it fires on your phone whether or not the app is running.

## Changing things later

| I want to… | Edit |
|---|---|
| Change what a fresh install starts with | `js/config.js` |
| Change the sweep checklist steps | `CONFIG.SWEEP_STEPS` in `js/config.js` |
| Point at a different Canvas | `CONFIG.CANVAS_URL` in `js/config.js` |
| Change how anything looks | `css/style.css` |
| Change behaviour | `js/app.js` (rendering) / `js/store.js` (data + shift logic) |

`js/config.js` only seeds a **brand-new** install. Once you've used the app, your
own data takes over — to pick up new config defaults, use
**Settings → Reset Everything** (this erases your tasks).

## Structure

```
index.html      page shell — markup only
css/style.css   all styling, light + dark
js/config.js    defaults: courses, shifts, sweep steps
js/store.js     localStorage state, date helpers, shift logic
js/app.js       rendering and interaction
```

No build step and no dependencies. Open `index.html`, or `npx serve .`.
