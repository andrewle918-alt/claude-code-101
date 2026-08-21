/* Claude Code 101 — app logic */
(function () {
  "use strict";

  const STORAGE_KEY = "cc101_progress_v1";
  const LAST_LESSON_KEY = "cc101_last_lesson_v1";

  const sidebarEl = document.getElementById("sidebar");
  const contentEl = document.getElementById("content");
  const progressFillEl = document.getElementById("progress-fill");
  const progressLabelEl = document.getElementById("progress-label");
  const resetBtn = document.getElementById("reset-progress");

  function loadCompleted() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? new Set(JSON.parse(raw)) : new Set();
    } catch (e) {
      return new Set();
    }
  }

  function saveCompleted(set) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...set]));
  }

  let completed = loadCompleted();
  let currentIndex = 0;

  const savedLast = localStorage.getItem(LAST_LESSON_KEY);
  if (savedLast) {
    const idx = LESSONS.findIndex((l) => l.id === savedLast);
    if (idx >= 0) currentIndex = idx;
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function renderSidebar() {
    sidebarEl.innerHTML = "";
    const label = document.createElement("div");
    label.className = "sidebar-group-label";
    label.textContent = "Lessons";
    sidebarEl.appendChild(label);

    LESSONS.forEach((lesson, i) => {
      const btn = document.createElement("button");
      btn.className = "lesson-link";
      if (i === currentIndex) btn.classList.add("active");
      if (completed.has(lesson.id)) btn.classList.add("done");
      btn.innerHTML = `
        <span class="lesson-num">${completed.has(lesson.id) ? "✓" : i + 1}</span>
        <span class="lesson-title">${escapeHtml(lesson.title)}</span>
      `;
      btn.addEventListener("click", () => goTo(i));
      sidebarEl.appendChild(btn);
    });
  }

  function updateProgress() {
    const total = LESSONS.length;
    const done = LESSONS.filter((l) => completed.has(l.id)).length;
    const pct = total ? Math.round((done / total) * 100) : 0;
    progressFillEl.style.width = pct + "%";
    progressLabelEl.textContent = `${done} / ${total} lessons`;
  }

  function renderBodyBlock(block) {
    switch (block.type) {
      case "p":
        return `<p>${block.text}</p>`;
      case "h3":
        return `<h3>${block.text}</h3>`;
      case "ul":
        return `<ul>${block.items.map((i) => `<li>${i}</li>`).join("")}</ul>`;
      case "ol":
        return `<ol>${block.items.map((i) => `<li>${i}</li>`).join("")}</ol>`;
      case "callout":
        return `<div class="callout">${block.title ? `<strong>${escapeHtml(block.title)}:</strong> ` : ""}${block.text}</div>`;
      case "code":
        return `<div class="codeblock">${block.lines
          .map((l) => {
            if (l.type === "comment") return `<span class="comment">${escapeHtml(l.text)}</span>`;
            if (l.type === "prompt") return `<span class="prompt">$ ${escapeHtml(l.text)}</span>`;
            return escapeHtml(l.text);
          })
          .join("\n")}</div>`;
      default:
        return "";
    }
  }

  function renderTryIt(lesson) {
    if (!lesson.tryIt) return "";
    const t = lesson.tryIt;
    return `
      <div class="tryit" id="tryit-box">
        <div class="tryit-header"><span class="dot" style="background:#7fd97f"></span> Simulated terminal</div>
        <div class="tryit-instructions">${escapeHtml(t.instructions)}</div>
        <div class="terminal" id="terminal-${lesson.id}">
          <div id="terminal-output-${lesson.id}"></div>
          <div class="terminal-line terminal-input-row" id="terminal-input-row-${lesson.id}">
            <span class="prompt-sym">&gt;</span>
            <input type="text" class="terminal-input" id="terminal-input-${lesson.id}"
                   placeholder="${escapeHtml(t.placeholder || "")}" autocomplete="off" spellcheck="false" />
            <button class="terminal-submit" id="terminal-submit-${lesson.id}">Run</button>
          </div>
        </div>
      </div>
    `;
  }

  function renderQuiz(lesson) {
    if (!lesson.quiz) return "";
    const q = lesson.quiz;
    return `
      <div class="quiz" id="quiz-box">
        <div class="quiz-label">Check your understanding</div>
        <div class="quiz-question">${escapeHtml(q.question)}</div>
        <form id="quiz-form">
          ${q.options
            .map(
              (opt, i) => `
            <label class="quiz-option" data-index="${i}">
              <input type="radio" name="quiz-opt" value="${i}" />
              <span>${escapeHtml(opt)}</span>
            </label>`
            )
            .join("")}
        </form>
        <button class="quiz-check-btn" id="quiz-check-btn">Check answer</button>
        <div class="quiz-feedback" id="quiz-feedback"></div>
      </div>
    `;
  }

  function renderLesson(index) {
    const lesson = LESSONS[index];
    const isDone = completed.has(lesson.id);

    contentEl.innerHTML = `
      <div class="lesson-kicker">${escapeHtml(lesson.kicker)}</div>
      <div class="lesson-header">
        <h1>${escapeHtml(lesson.title)}</h1>
        <p class="lesson-subtitle">${escapeHtml(lesson.subtitle)}</p>
      </div>
      <div class="lesson-body">
        ${lesson.body.map(renderBodyBlock).join("")}
        ${renderTryIt(lesson)}
        ${renderQuiz(lesson)}
        <div class="mark-complete-row">
          <span class="complete-check ${isDone ? "show" : ""}" id="complete-check">✓ Lesson complete</span>
        </div>
      </div>
      <div class="lesson-nav">
        <button class="nav-btn" id="prev-btn" ${index === 0 ? "disabled" : ""}>
          <span class="nav-btn-label">Previous</span>
          ${index > 0 ? escapeHtml(LESSONS[index - 1].title) : "—"}
        </button>
        <button class="nav-btn primary" id="next-btn">
          <span class="nav-btn-label">${index === LESSONS.length - 1 ? "Finish" : "Next"}</span>
          ${index < LESSONS.length - 1 ? escapeHtml(LESSONS[index + 1].title) : "See your summary"}
        </button>
      </div>
    `;

    wireLessonInteractions(lesson);

    document.getElementById("prev-btn").addEventListener("click", () => goTo(index - 1));
    document.getElementById("next-btn").addEventListener("click", () => {
      if (index === LESSONS.length - 1) {
        renderCompletionScreen();
      } else {
        goTo(index + 1);
      }
    });

    window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });
  }

  function markComplete(lesson) {
    if (!completed.has(lesson.id)) {
      completed.add(lesson.id);
      saveCompleted(completed);
      updateProgress();
      renderSidebar();
      const check = document.getElementById("complete-check");
      if (check) check.classList.add("show");
    }
  }

  function wireLessonInteractions(lesson) {
    // Try-it terminal
    if (lesson.tryIt) {
      const t = lesson.tryIt;
      const input = document.getElementById(`terminal-input-${lesson.id}`);
      const submitBtn = document.getElementById(`terminal-submit-${lesson.id}`);
      const output = document.getElementById(`terminal-output-${lesson.id}`);
      const inputRow = document.getElementById(`terminal-input-row-${lesson.id}`);

      let solved = false;

      const run = () => {
        const val = input.value.trim();
        if (!val) return;

        const echoLine = document.createElement("div");
        echoLine.className = "terminal-line";
        echoLine.innerHTML = `<span class="prompt-sym">&gt;</span><span>${escapeHtml(val)}</span>`;
        output.appendChild(echoLine);

        const matched = t.accept.some((re) => re.test(val));
        const outLine = document.createElement("div");

        if (matched) {
          let text, ok = true;
          if (t.respond) {
            const r = t.respond(val);
            text = r.text;
            ok = r.ok;
          } else {
            text = t.success;
          }
          outLine.className = "terminal-output success";
          outLine.textContent = text;
          output.appendChild(outLine);
          input.value = "";

          if (!solved) {
            solved = true;
            const banner = document.createElement("div");
            banner.className = "tryit-solved-banner";
            banner.textContent = "✓ Nice — you got it.";
            document.getElementById("tryit-box").appendChild(banner);
          }
        } else {
          outLine.className = "terminal-output hint";
          outLine.textContent = t.hint;
          output.appendChild(outLine);
          input.value = "";
        }
        inputRow.scrollIntoView({ block: "nearest" });
      };

      submitBtn.addEventListener("click", run);
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") run();
      });
    }

    // Quiz
    if (lesson.quiz) {
      const q = lesson.quiz;
      const checkBtn = document.getElementById("quiz-check-btn");
      const feedback = document.getElementById("quiz-feedback");
      const optionLabels = [...document.querySelectorAll(".quiz-option")];
      let answered = false;

      checkBtn.addEventListener("click", () => {
        const selected = document.querySelector('input[name="quiz-opt"]:checked');
        if (!selected) {
          feedback.className = "quiz-feedback show incorrect";
          feedback.textContent = "Pick an answer first.";
          return;
        }
        const idx = parseInt(selected.value, 10);
        const isCorrect = idx === q.correct;

        optionLabels.forEach((label) => {
          const i = parseInt(label.dataset.index, 10);
          label.classList.remove("correct", "incorrect");
          if (i === q.correct) label.classList.add("correct");
          else if (i === idx && !isCorrect) label.classList.add("incorrect");
        });

        feedback.className = "quiz-feedback show " + (isCorrect ? "correct" : "incorrect");
        feedback.textContent = (isCorrect ? "Correct. " : "Not quite. ") + q.explanation;

        if (!answered) {
          answered = true;
          markComplete(lesson);
        }
      });
    }
  }

  function renderCompletionScreen() {
    contentEl.innerHTML = `
      <div class="completion-screen">
        <div class="big-emoji">🎉</div>
        <h1>You've completed the basics.</h1>
        <p>You now know what Claude Code is, how to install and start it, how to talk
           to it effectively, how it edits files, how permissions keep you in control,
           the key slash commands, and how it handles git. That's the real foundation —
           everything else is just practice.</p>
        <p style="font-size:13px;">Ready for more? Try running <code>claude</code> in one of your own
           projects and ask it to explain the codebase to you.</p>
        <button class="nav-btn primary" id="review-btn" style="max-width:none; display:inline-block; margin-top:8px;">
          <span class="nav-btn-label">Review</span>
          Back to Lesson 1
        </button>
      </div>
    `;
    document.getElementById("review-btn").addEventListener("click", () => goTo(0));
    renderSidebar();
    window.scrollTo({ top: 0 });
  }

  function goTo(index) {
    currentIndex = Math.max(0, Math.min(LESSONS.length - 1, index));
    localStorage.setItem(LAST_LESSON_KEY, LESSONS[currentIndex].id);
    renderSidebar();
    renderLesson(currentIndex);
    updateProgress();
  }

  resetBtn.addEventListener("click", () => {
    if (confirm("Reset your progress? This clears all completed lessons.")) {
      completed = new Set();
      saveCompleted(completed);
      localStorage.removeItem(LAST_LESSON_KEY);
      currentIndex = 0;
      renderSidebar();
      renderLesson(currentIndex);
      updateProgress();
    }
  });

  // init
  renderSidebar();
  renderLesson(currentIndex);
  updateProgress();
})();
