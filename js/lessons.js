/* Claude Code 101 — lesson content
 * Each lesson is plain data. app.js renders it and handles the interactive bits.
 */

const LESSONS = [

// ---------------------------------------------------------------- 1
{
  id: "welcome",
  kicker: "Lesson 1",
  title: "What is Claude Code?",
  subtitle: "The 60-second version before you touch a keyboard.",
  body: [
    { type: "p", text: "Claude Code is a command-line tool from Anthropic. You run it inside a project folder on your computer, and you talk to it in plain English. It reads your files, writes and edits code, runs terminal commands, and generally acts like a very fast, very literal junior engineer who is sitting at your keyboard." },
    { type: "p", text: "It is <strong>not</strong> a website or a chat window in a browser. It lives in your terminal, and it works directly on the real files in your real project — so anything it changes, you'll see reflected on disk immediately." },
    { type: "h3", text: "What can it actually do?" },
    { type: "ul", items: [
      "Read and understand an entire codebase, even one it's never seen before.",
      "Write new code, fix bugs, and refactor — across many files at once.",
      "Run terminal commands: install packages, run tests, start servers.",
      "Search the web for docs, and read files like PDFs or images.",
      "Use <code>git</code> and GitHub: commit, branch, open pull requests.",
    ]},
    { type: "callout", title: "Key idea", text: "You are always the one in charge. Claude Code proposes changes and asks for your permission before doing anything risky — you'll learn exactly how that works in Lesson 6." },
  ],
  quiz: {
    question: "Where does Claude Code run?",
    options: [
      "In a browser tab, like ChatGPT",
      "In your terminal, directly inside a project folder on your computer",
      "Only inside GitHub's website",
      "It's a Photoshop plugin",
    ],
    correct: 1,
    explanation: "Claude Code is a CLI (command-line interface) tool. You launch it from your terminal inside a project directory, and it operates on the real files there.",
  },
},

// ---------------------------------------------------------------- 2
{
  id: "install",
  kicker: "Lesson 2",
  title: "Installing Claude Code",
  subtitle: "Get it onto your machine and log in.",
  body: [
    { type: "p", text: "Claude Code is distributed as an npm package, so you need <strong>Node.js</strong> (version 18 or newer) installed first. If you're not sure whether you have it, check:" },
    { type: "code", lines: [
      { type: "prompt", text: "node --version" },
    ]},
    { type: "p", text: "If that prints a version number ≥ 18, you're set. If not, install Node.js from nodejs.org first. Then install Claude Code globally:" },
    { type: "code", lines: [
      { type: "prompt", text: "npm install -g @anthropic-ai/claude-code" },
    ]},
    { type: "h3", text: "Logging in" },
    { type: "p", text: "Navigate into a project folder and start it up:" },
    { type: "code", lines: [
      { type: "prompt", text: "cd my-project" },
      { type: "prompt", text: "claude" },
    ]},
    { type: "p", text: "The first time you run it, it'll walk you through logging in — either with your Claude.ai account (if you have a Pro or Max subscription) or with an API key from the Anthropic Console (pay-as-you-go billing). Pick whichever you already have; you can always change it later." },
    { type: "callout", title: "Tip", text: "Run <code>claude</code> from inside the folder you want to work on. Claude Code treats your current directory as its \"workspace\" — that's the scope of what it can see and edit by default." },
  ],
  tryIt: {
    instructions: "Try it: type the command that installs Claude Code globally with npm.",
    placeholder: "type a command…",
    accept: [/npm\s+install\s+(-g|--global)\s+@anthropic-ai\/claude-code/i, /npm\s+i\s+(-g|--global)\s+@anthropic-ai\/claude-code/i],
    success: "Package installed globally.\n\n+ @anthropic-ai/claude-code@latest\nadded 1 package in 2s\n\nRun 'claude' in any project folder to get started.",
    hint: "Not quite — remember it's an npm global install of the package @anthropic-ai/claude-code. Try: npm install -g @anthropic-ai/claude-code",
  },
  quiz: {
    question: "What determines which files and folders Claude Code can see by default?",
    options: [
      "It can see your entire computer automatically",
      "The directory you were in when you ran the `claude` command",
      "You have to manually upload files one by one",
      "It only works on files already pushed to GitHub",
    ],
    correct: 1,
    explanation: "Claude Code scopes itself to your current working directory — wherever you ran `claude` from is treated as the project workspace.",
  },
},

// ---------------------------------------------------------------- 3
{
  id: "first-session",
  kicker: "Lesson 3",
  title: "Your first session",
  subtitle: "What actually happens when you launch it.",
  body: [
    { type: "p", text: "Once you run <code>claude</code>, you land in an interactive prompt inside your terminal — this is sometimes called the REPL. There's no menu to learn. You just type what you want in plain English and press Enter." },
    { type: "p", text: "A great first message in any new project is simply asking it to look around:" },
    { type: "code", lines: [
      { type: "comment", text: "# a good first message in a new project" },
      { type: "text", text: "> What does this project do, and how is it structured?" },
    ]},
    { type: "p", text: "Claude will read through your files (package.json, source folders, README, etc.) and give you a summary — before it changes a single thing. This costs you nothing but a few seconds and gives you a sanity check that it understands your codebase." },
    { type: "h3", text: "Ending a session" },
    { type: "p", text: "Press <code>Ctrl+C</code> twice, or type <code>exit</code>, to leave. Your conversation isn't lost forever — Claude Code keeps session history you can resume later with <code>claude --continue</code> or <code>claude --resume</code>." },
    { type: "callout", title: "Interrupting", text: "If Claude is in the middle of doing something and you want it to stop — say you realize you asked for the wrong thing — just press <code>Esc</code>. You can then redirect it." },
  ],
  tryIt: {
    instructions: "Try it: this simulated terminal already has Claude Code running. Ask it what the project does.",
    placeholder: "ask a question…",
    accept: [/what.*(project|repo|codebase|this).*(do|about|structure)/i, /explain.*(project|codebase|repo)/i, /describe.*(project|codebase|repo)/i],
    success: "Reading project files… (package.json, src/, README.md)\n\nThis is a small Express.js API with a React frontend. It exposes\nREST endpoints under /api and stores data in a local SQLite file.\nThe frontend is a Vite + React app in /client.\n\nWant a more detailed breakdown of any part?",
    hint: "Try asking something like: \"What does this project do?\"",
  },
  quiz: {
    question: "You accidentally asked Claude to do the wrong thing and it has started working. What do you do?",
    options: [
      "Close the entire terminal window",
      "Press Esc to interrupt it, then explain what you actually meant",
      "Nothing — once started it can't be stopped",
      "Uninstall Claude Code",
    ],
    correct: 1,
    explanation: "Esc interrupts the current action cleanly. You can then just tell it what you actually meant — no need to restart anything.",
  },
},

// ---------------------------------------------------------------- 4
{
  id: "prompting",
  kicker: "Lesson 4",
  title: "Writing good prompts",
  subtitle: "Same rules as delegating to a sharp new hire.",
  body: [
    { type: "p", text: "Claude Code is very capable, but it can't read your mind. The number one skill to build is giving it the same context you'd give a new teammate: what you want, any constraints, and how to know it's done." },
    { type: "h3", text: "Vague vs. specific" },
    { type: "code", lines: [
      { type: "comment", text: "# vague — Claude has to guess a lot" },
      { type: "text", text: "> fix the bug" },
      { type: "comment", text: "" },
      { type: "comment", text: "# specific — Claude can act immediately" },
      { type: "text", text: "> Users report the login form submits twice when they double-click" },
      { type: "text", text: "  Submit. Find where the submit handler lives and stop that." },
    ]},
    { type: "ul", items: [
      "<strong>Give it the symptom, not just the diagnosis</strong> — describe what's wrong, and let Claude investigate. It's often better at finding root causes than you'd expect.",
      "<strong>Point it at files or errors</strong> — paste an error message, a stack trace, or say \"look at src/auth/login.ts\".",
      "<strong>Break big asks into steps</strong> — \"Add user authentication\" is a project; \"Add a POST /login route that checks the password hash\" is a task.",
      "<strong>Say what \"done\" looks like</strong> — \"...and make sure the existing tests still pass\" gives Claude a way to check its own work.",
    ]},
    { type: "callout", title: "It's a conversation", text: "You don't need the perfect prompt on the first try. Claude Code is conversational — you can correct it, add detail, or say \"actually, do it this way instead\" at any point." },
  ],
  tryIt: {
    instructions: "Try it: rewrite a vague request. Ask Claude to fix a \"broken button\" but give it a specific, useful detail.",
    placeholder: "e.g. the checkout button doesn't work when the cart is empty",
    accept: [/.{25,}/],
    success: "Got it — that's specific enough to act on. I'll look at the checkout\ncomponent's click handler and the empty-cart state first.\n\n(In a real session, Claude would now read the relevant files and\npropose a fix.)",
    hint: "Add a bit more detail — what page or component, and what actually happens when it 'doesn't work'? Aim for at least a full sentence.",
  },
  quiz: {
    question: "Which of these prompts will get you the best result?",
    options: [
      "\"make it better\"",
      "\"fix everything\"",
      "\"the /export button throws a 500 error when the report has zero rows — find and fix it\"",
      "\"you know what to do\"",
    ],
    correct: 2,
    explanation: "Specific symptoms, a concrete trigger, and a clear ask let Claude act immediately instead of guessing what you mean.",
  },
},

// ---------------------------------------------------------------- 5
{
  id: "editing",
  kicker: "Lesson 5",
  title: "How Claude edits your files",
  subtitle: "Diffs, review, and staying in the loop.",
  body: [
    { type: "p", text: "When Claude Code wants to change a file, it doesn't just silently overwrite it. It shows you a <strong>diff</strong> — the exact lines being added or removed — before, or as, the change is applied, so you can see precisely what's happening." },
    { type: "code", lines: [
      { type: "comment", text: "# example diff shown in your terminal" },
      { type: "text", text: "  function total(items) {" },
      { type: "text", text: "-   return items.length;" },
      { type: "text", text: "+   return items.reduce((sum, i) => sum + i.price, 0);" },
      { type: "text", text: "  }" },
    ]},
    { type: "p", text: "Lines starting with <code>-</code> are being removed, lines with <code>+</code> are being added — this is the same format used by <code>git diff</code>, so it'll look familiar if you've used version control before." },
    { type: "h3", text: "New files vs. edits" },
    { type: "ul", items: [
      "For a brand-new file, Claude will show you the full content it's about to create.",
      "For an existing file, it shows just the changed lines in context, not the whole file.",
      "You can always ask \"show me the whole file\" if you want the complete picture.",
    ]},
    { type: "callout", title: "You're always reviewing", text: "Treat Claude's edits the way you'd treat a coworker's pull request: skim the diff, and if something looks off, say so before it goes further. It's much cheaper to redirect early than to unwind five files later." },
  ],
  quiz: {
    question: "In a diff, what does a line starting with a minus sign (-) mean?",
    options: [
      "That line is being added",
      "That line is being deleted / removed",
      "That line has a syntax error",
      "That line is a comment",
    ],
    correct: 1,
    explanation: "Standard diff convention: `-` = removed, `+` = added. This is the same format `git diff` uses.",
  },
},

// ---------------------------------------------------------------- 6
{
  id: "permissions",
  kicker: "Lesson 6",
  title: "Permissions & staying in control",
  subtitle: "How Claude Code asks before it acts.",
  body: [
    { type: "p", text: "By default, Claude Code pauses and asks for your approval before doing anything that changes something: editing a file, running a shell command, installing a package. You'll see a prompt like <code>Allow this action? (y/n)</code> and nothing happens until you answer." },
    { type: "p", text: "You control how cautious it is:" },
    { type: "ul", items: [
      "<strong>Default mode</strong> — asks before every file edit and every terminal command. Best for your first few sessions.",
      "<strong>Auto-accept edits</strong> — stops asking about file edits (still asks about things like running commands), for when you trust it on a routine task.",
      "<strong>Plan mode</strong> — Claude can only read and research, not change anything, until it presents you a plan and you approve it. Great for big or risky changes. Toggle modes with <code>Shift+Tab</code>.",
    ]},
    { type: "p", text: "You can also pre-approve specific, safe commands (like <code>npm test</code>) so it stops asking about that one thing specifically, via <code>/permissions</code>." },
    { type: "callout", title: "Why this matters", text: "Claude Code can run real commands on your real machine — including things like deleting files or pushing to git. The permission system is what keeps you the decision-maker. As a beginner, stay in default mode and actually read what you're approving." },
  ],
  tryIt: {
    instructions: "Try it: Claude wants to run a command that will delete a file. Type 'n' to reject it, or 'y' to approve — see what happens either way.",
    placeholder: "y or n",
    accept: [/^y(es)?$/i, /^n(o)?$/i],
    respond: (input) => {
      if (/^y(es)?$/i.test(input)) {
        return { ok: true, text: "rm old-report.csv\n\nDeleted old-report.csv.\n\n(This is why the prompt matters — always glance at the\ncommand before approving it.)" };
      }
      return { ok: true, text: "Rejected. old-report.csv was not touched.\n\n> Understood — I won't run that. Let me know how you'd\n  like to handle it instead." };
    },
    hint: "Type just 'y' or 'n'.",
  },
  quiz: {
    question: "What is 'plan mode' for?",
    options: [
      "It makes Claude type faster",
      "It lets Claude read and research but not make any changes, until you approve a plan",
      "It's a paid subscription tier",
      "It automatically deploys your code",
    ],
    correct: 1,
    explanation: "Plan mode is a read-only research phase — Claude investigates and proposes an approach, and nothing is changed on disk until you approve it.",
  },
},

// ---------------------------------------------------------------- 7
{
  id: "slash-commands",
  kicker: "Lesson 7",
  title: "Slash commands & CLAUDE.md",
  subtitle: "The handful of shortcuts worth knowing on day one.",
  body: [
    { type: "p", text: "Typed at the prompt, slash commands are special instructions to Claude Code itself, rather than requests about your code. Here are the ones you'll actually use early on:" },
    { type: "ul", items: [
      "<code>/help</code> — list available commands.",
      "<code>/clear</code> — wipe the current conversation and start fresh (useful when switching to an unrelated task).",
      "<code>/compact</code> — summarize the conversation so far to free up space, while keeping the important context.",
      "<code>/init</code> — scans your project and generates a <code>CLAUDE.md</code> file (see below).",
      "<code>/permissions</code> — view and edit what Claude is allowed to do without asking.",
      "<code>/model</code> — switch which Claude model you're using.",
    ]},
    { type: "h3", text: "CLAUDE.md — your project's memory" },
    { type: "p", text: "<code>CLAUDE.md</code> is just a markdown file you keep at the root of your project. Claude Code automatically reads it at the start of every session. Use it for things you'd otherwise repeat every time: coding conventions, how to run tests, which package manager you use, things to never touch." },
    { type: "code", lines: [
      { type: "comment", text: "# example CLAUDE.md" },
      { type: "text", text: "- Use pnpm, not npm or yarn" },
      { type: "text", text: "- Run `pnpm test` before considering any task done" },
      { type: "text", text: "- Never edit files under /generated — they're auto-generated" },
      { type: "text", text: "- We use 2-space indentation and no semicolons" },
    ]},
    { type: "callout", title: "Tip", text: "Run <code>/init</code> in a new project and let Claude draft the first version of CLAUDE.md for you — then edit it by hand to add anything project-specific it couldn't infer." },
  ],
  tryIt: {
    instructions: "Try it: type the slash command that generates a CLAUDE.md file for the current project.",
    placeholder: "type a slash command…",
    accept: [/^\/init$/i],
    success: "Scanning project…\n\nCreated CLAUDE.md with:\n- Detected stack: Node.js, Express, React\n- Package manager: npm\n- Test command: npm test\n\nFeel free to edit it — add anything project-specific.",
    hint: "The command is exactly: /init",
  },
  quiz: {
    question: "What is CLAUDE.md for?",
    options: [
      "It's Claude Code's changelog",
      "A project file Claude reads automatically each session, for conventions and instructions you'd otherwise repeat",
      "It's required for Claude Code to install",
      "It's a license file",
    ],
    correct: 1,
    explanation: "CLAUDE.md is project memory — persistent context and rules Claude reads automatically, so you don't have to restate them every session.",
  },
},

// ---------------------------------------------------------------- 8
{
  id: "git-github",
  kicker: "Lesson 8",
  title: "Git & GitHub basics",
  subtitle: "Letting Claude handle version control for you.",
  body: [
    { type: "p", text: "Claude Code can run <code>git</code> commands directly (with your approval, per Lesson 6), which means you can hand off the entire commit/branch/PR workflow in plain English instead of memorizing git syntax." },
    { type: "code", lines: [
      { type: "text", text: "> commit these changes with a clear message" },
      { type: "comment", text: "" },
      { type: "text", text: "> create a new branch called fix/login-bug and switch to it" },
      { type: "comment", text: "" },
      { type: "text", text: "> open a pull request for this branch" },
    ]},
    { type: "p", text: "For commits, Claude looks at the actual diff and writes a message describing it — you'll still see and approve the exact message before it runs. For pull requests, it uses the GitHub CLI (<code>gh</code>) if you have it installed and authenticated." },
    { type: "callout", title: "Good habit", text: "Ask Claude to run <code>git status</code> and <code>git diff</code> before committing anything, if you're ever unsure what's about to be staged. It's a normal, cheap thing to ask for." },
    { type: "p", text: "One important boundary: Claude Code will not silently force-push, rewrite history, or push straight to a protected branch like <code>main</code> — those are the kinds of actions it'll flag for extra confirmation, because they're hard to undo." },
  ],
  tryIt: {
    instructions: "Try it: ask Claude, in plain English, to commit the current changes.",
    placeholder: "ask for a commit…",
    accept: [/commit/i],
    success: "git diff\n\n  src/api/login.ts | 12 +++++++-----\n\nProposed commit message:\n\n  \"Fix double-submit bug on login form\"\n\nRun this commit? (y/n)",
    hint: "Just describe what you want in plain English — try something like \"commit these changes\".",
  },
  quiz: {
    question: "How do you typically get Claude Code to make a git commit?",
    options: [
      "You can't — you must switch to a separate terminal",
      "Ask it in plain English (e.g. \"commit this\"); it drafts a message from the diff and asks you to approve running it",
      "It commits automatically after every single file edit, no way to stop it",
      "You have to write the git command yourself and paste it in",
    ],
    correct: 1,
    explanation: "You describe the intent in plain English; Claude looks at the actual diff, proposes a commit message, and still asks for approval before running git.",
  },
},

// ---------------------------------------------------------------- 9
{
  id: "best-practices",
  kicker: "Lesson 9",
  title: "Best practices cheat sheet",
  subtitle: "The habits that separate a smooth session from a messy one.",
  body: [
    { type: "h3", text: "Do" },
    { type: "ul", items: [
      "<strong>Start small.</strong> Give Claude one clear task, see the result, then ask for the next thing — rather than one giant vague request.",
      "<strong>Read the diffs.</strong> You're the reviewer. A ten-second skim catches most issues before they compound.",
      "<strong>Use plan mode for anything risky</strong> — big refactors, deleting things, touching production config.",
      "<strong>Keep CLAUDE.md updated</strong> as your project's conventions evolve — it saves you from repeating yourself.",
      "<strong>Use <code>/clear</code> between unrelated tasks</strong> so old context doesn't confuse a new one.",
    ]},
    { type: "h3", text: "Avoid" },
    { type: "ul", items: [
      "<strong>Don't blindly approve everything.</strong> The permission prompts exist for a reason — actually look at what you're allowing.",
      "<strong>Don't skip context.</strong> \"Fix the bug\" with no detail wastes both your time and Claude's investigation effort.",
      "<strong>Don't fight the tool in one giant prompt.</strong> If a request feels like it needs five paragraphs, it's probably five separate tasks.",
    ]},
    { type: "callout", title: "You're ready", text: "That's the whole foundation: install it, talk to it plainly, review its diffs, and stay in control of what it's allowed to run. Everything else — subagents, custom skills, hooks, MCP integrations — builds on exactly these basics." },
  ],
  quiz: {
    question: "You need Claude to do something fairly large and a bit risky (say, upgrading a major dependency across the codebase). What's the best approach?",
    options: [
      "One giant prompt describing the entire migration at once, auto-accept everything",
      "Use plan mode first so Claude proposes an approach before changing anything, then work through it in reviewable steps",
      "Do it yourself instead — Claude Code can't handle multi-file changes",
      "Delete the project and start over",
    ],
    correct: 1,
    explanation: "For risky or large changes, plan mode lets you see and approve the approach before any file changes happen, and breaking it into steps keeps each diff reviewable.",
  },
},

];
