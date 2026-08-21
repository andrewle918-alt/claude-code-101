# Claude Code 101

A free, interactive, hands-on tutorial that teaches Claude Code from zero — no prior experience assumed.

It's a plain static site (HTML/CSS/JS, no build step, no dependencies) with:

- 9 short lessons covering install → first session → prompting → file edits → permissions → slash commands/CLAUDE.md → git basics → best practices
- A simulated terminal in several lessons so you can practice typing real commands and see canned-but-realistic output
- A short quiz at the end of each lesson
- Progress is saved in your browser (`localStorage`) so you can close the tab and pick up where you left off

## Run it locally

No build step needed — just open `index.html` in a browser, or serve it:

```bash
npx serve .
```

## Deploy to GitHub Pages

1. Push this folder to a new GitHub repo.
2. In the repo, go to **Settings → Pages → Build and deployment → Source**, and choose **GitHub Actions**.
3. Push to `main` — the included workflow (`.github/workflows/deploy.yml`) builds and deploys automatically.

Your site will be live at `https://<your-username>.github.io/<repo-name>/`.

## Project structure

```
index.html          entry point / page shell
css/style.css        all styling (light + dark mode aware)
js/lessons.js         lesson content as data
js/app.js             rendering, quiz logic, progress tracking, simulated terminal
```

Lesson content lives entirely in `js/lessons.js` — add a new lesson by adding a new object to the `LESSONS` array; no other file needs to change.
