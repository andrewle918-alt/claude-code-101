/* Sweep — rendering and interaction. */

const $  = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const esc = s => String(s ?? "").replace(/[&<>"']/g, c =>
  ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c]));

let view = "today";

/* ---------------- boot ---------------- */

function boot() {
  $("#app").hidden = false;
  bindChrome();
  render();
  // Keep the shift banner honest without a page reload.
  setInterval(() => { renderMasthead(); renderBanner(); }, 30_000);
}

function render() {
  renderMasthead();
  renderBanner();
  renderSetup();
  renderSegmented();
  renderView();
}

/* ---------------- masthead ---------------- */

function renderMasthead() {
  const now = new Date();
  $("#eyebrow").textContent =
    now.toLocaleDateString(undefined, { weekday:"long", month:"long", day:"numeric" }).toUpperCase();

  const open = Store.get().tasks.filter(t => !t.done);
  const overdue = open.filter(t => t.due && D.daysUntil(t.due) < 0).length;
  const todayCount = open.filter(t => t.due && D.daysUntil(t.due) === 0).length;

  let line;
  if (!open.length)      line = "Nothing on the list. Enjoy it.";
  else if (overdue)      line = `${overdue} overdue · ${open.length} open`;
  else if (todayCount)   line = `${todayCount} due today · ${open.length} open`;
  else                   line = `${open.length} open task${open.length === 1 ? "" : "s"}`;
  $("#subtitle").textContent = line;
}

/* ---------------- the Access One reminder ---------------- */

function renderBanner() {
  const el = $("#shift-banner");
  const wk = D.weekKey();
  const current = Shifts.current();

  if (current) {
    const key = `${wk}|${current.id}`;
    if (Store.get().dismissed[key]) { el.hidden = true; return; }

    const done = sweepProgress(wk);
    const left = done.coursesLeft;
    el.hidden = false;
    el.className = "banner banner-live";
    el.innerHTML = `
      <div class="banner-pulse" aria-hidden="true"></div>
      <div class="banner-text">
        <p class="banner-kicker">${esc(Shifts.accessOneSummary(current) || "Access One")} · until ${esc(D.time(current.end))}</p>
        <h2>Start with Canvas.</h2>
        <p class="banner-sub">${left > 0
          ? `${left} course${left === 1 ? "" : "s"} left to sweep for this week's tasks.`
          : `This week's sweep is done. Pick something off the list.`}</p>
      </div>
      <div class="banner-actions">
        <button class="btn-primary" data-goto="sweep">${done.count ? "Continue sweep" : "Begin sweep"}</button>
        <button class="btn-quiet" data-dismiss="${esc(key)}">Not now</button>
      </div>`;
    return;
  }

  const next = Shifts.next();
  if (next) {
    el.hidden = false;
    el.className = "banner banner-upcoming";
    el.innerHTML = `
      <div class="banner-text">
        <p class="banner-kicker">Next Access One</p>
        <h2>${esc(D.dayName(next.shift.day))}, ${esc(D.time(next.shift.start))}</h2>
        <p class="banner-sub">${esc(Shifts.countdown(next.mins))} — ${esc(D.time(next.shift.start))} to ${esc(D.time(next.shift.end))}${
          Shifts.accessOneSummary(next.shift) ? ` · ${esc(Shifts.accessOneSummary(next.shift))}` : ""}</p>
      </div>`;
    return;
  }

  el.hidden = true;
}

/* ---------------- first-run setup ---------------- */

function renderSetup() {
  const el = $("#setup-card");
  const s = Store.get();

  if (s.shifts.length === 0) {
    el.hidden = false;
    el.innerHTML = `
      <h2>One thing first</h2>
      <p>Sweep reminds you to check Canvas <strong>only</strong> when an Access One shift starts. Add your shifts and mark which ones are Access One.</p>
      <div class="setup-actions">
        <button class="btn-primary" data-open-settings="shifts">Set up my shifts</button>
      </div>
      <p class="setup-fine">Your schedule stays in this browser. It is never uploaded, and it is not in the app's code.</p>`;
    return;
  }

  if (!s.shifts.some(x => Shifts.reminders(x).length)) {
    el.hidden = false;
    el.innerHTML = `
      <h2>No reminders set</h2>
      <p>You have ${s.shifts.length} shift${s.shifts.length === 1 ? "" : "s"} saved, but none of them has a reminder yet — so nothing will ping you.</p>
      <div class="setup-actions">
        <button class="btn-primary" data-open-settings="shifts">Add one</button>
      </div>`;
    return;
  }

  el.hidden = true;
}

/* ---------------- segmented control ---------------- */

function renderSegmented() {
  $$(".seg").forEach(b => {
    const on = b.dataset.view === view;
    b.classList.toggle("is-on", on);
    b.setAttribute("aria-selected", String(on));
  });
}

/* ---------------- views ---------------- */

function renderView() {
  const el = $("#view");
  el.innerHTML =
      view === "sweep" ? viewSweep()
    : view === "week"  ? viewWeek()
    : view === "all"   ? viewAll()
    :                    viewToday();
}

function viewToday() {
  const tasks = Store.get().tasks.filter(t => !t.done);
  const overdue = tasks.filter(t => t.due && D.daysUntil(t.due) < 0);
  const due     = tasks.filter(t => t.due && D.daysUntil(t.due) === 0);
  const flagged = tasks.filter(t => t.flagged && !overdue.includes(t) && !due.includes(t));
  const shiftsToday = Shifts.onDay(new Date().getDay());

  let html = "";

  if (shiftsToday.length) {
    html += `<section class="strip">${shiftsToday.map(s => `
      <div class="strip-item ${s.accessOne ? "is-access" : ""}">
        <span class="strip-time">${esc(D.time(s.start))}–${esc(D.time(s.end))}</span>
        <span class="strip-label">${esc(Shifts.accessOneSummary(s) || rolesLabel(s))}</span>
      </div>`).join("")}</section>`;
  }

  if (!overdue.length && !due.length && !flagged.length) {
    html += empty("Clear for today", "Nothing due and nothing flagged. Add what's next, or run a sweep.");
    return html;
  }

  if (overdue.length) html += group("Overdue", overdue, "danger");
  if (due.length)     html += group("Due today", due);
  if (flagged.length) html += group("Flagged", flagged);
  return html;
}

function viewWeek() {
  const start = D.startOfWeek();
  const open = Store.get().tasks.filter(t => !t.done);
  let html = "";

  const past = open.filter(t => t.due && D.parse(t.due) < start);
  if (past.length) html += group("Carried over", past, "danger");

  for (let i = 0; i < 7; i++) {
    const day = D.addDays(start, i);
    const key = D.iso(day);
    const dayTasks = open.filter(t => t.due === key);
    const shifts = Shifts.onDay(day.getDay());
    const isToday = key === D.iso(D.today());

    html += `<section class="day ${isToday ? "is-today" : ""}">
      <header class="day-head">
        <h3>${esc(day.toLocaleDateString(undefined, { weekday:"long" }))}</h3>
        <span class="day-date">${esc(day.toLocaleDateString(undefined, { month:"short", day:"numeric" }))}</span>
      </header>
      ${shifts.map(s => `<p class="day-shift ${s.accessOne ? "is-access" : ""}">
          ${esc(D.time(s.start))}–${esc(D.time(s.end))} · ${esc(Shifts.accessOneSummary(s) || rolesLabel(s))}
        </p>`).join("")}
      ${dayTasks.length
        ? `<ul class="list">${dayTasks.map(taskRow).join("")}</ul>`
        : `<p class="day-empty">—</p>`}
    </section>`;
  }

  const someday = open.filter(t => !t.due);
  if (someday.length) html += group("No date", someday);
  return html;
}

function viewAll() {
  const s = Store.get();
  const open = s.tasks.filter(t => !t.done);
  const done = s.tasks.filter(t => t.done).sort((a,b) => (b.doneAt||0) - (a.doneAt||0));
  let html = "";

  if (!s.tasks.length) return empty("No tasks yet", "Tap Add a task, or run this week's sweep to pull them out of Canvas.");

  for (const c of s.courses) {
    const mine = open.filter(t => t.courseId === c.id);
    if (mine.length) html += group(c.name, sortByDue(mine));
  }
  const loose = open.filter(t => !s.courses.some(c => c.id === t.courseId));
  if (loose.length) html += group("Everything else", sortByDue(loose));

  if (done.length) {
    html += `<section class="group">
      <header class="group-head">
        <h3>Completed</h3>
        <button class="link-btn" id="clear-done">Clear</button>
      </header>
      <ul class="list">${done.slice(0, 40).map(taskRow).join("")}</ul>
    </section>`;
  }
  return html;
}

function viewSweep() {
  const s = Store.get();
  const wk = D.weekKey();
  const done = sweepProgress(wk);
  const pct = done.total ? Math.round(done.count / done.total * 100) : 0;

  if (!s.courses.length) {
    return empty("No courses yet", "Add your courses in Settings and the sweep will walk you through each one.");
  }

  let html = `
    <section class="sweep-head">
      <p class="eyebrow">WEEK OF ${esc(D.startOfWeek().toLocaleDateString(undefined,{month:"long",day:"numeric"}).toUpperCase())}</p>
      <h2>${done.count === done.total ? "Sweep complete." : "Work through Canvas, course by course."}</h2>
      <div class="progress"><div class="progress-fill" style="width:${pct}%"></div></div>
      <p class="progress-label">${done.count} of ${done.total} checks done</p>
      <a class="btn-primary" href="${esc(CONFIG.CANVAS_URL)}" target="_blank" rel="noopener">Open Canvas</a>
    </section>`;

  for (const c of s.courses) {
    const marks = (s.sweeps[wk] || {})[c.id] || {};
    const finished = CONFIG.SWEEP_STEPS.every(st => marks[st.id]);
    html += `<section class="sweep-course ${finished ? "is-done" : ""}">
      <header class="sweep-course-head">
        <span class="dot" style="background:${esc(c.color)}"></span>
        <h3>${esc(c.name)}</h3>
        ${finished ? `<span class="check-mark" aria-label="Complete">✓</span>` : ""}
      </header>
      <ul class="steps">
        ${CONFIG.SWEEP_STEPS.map(st => `
          <li>
            <label class="step">
              <input type="checkbox" class="tick" data-sweep="${esc(c.id)}" data-step="${esc(st.id)}" ${marks[st.id] ? "checked" : ""}>
              <span class="step-text"><strong>${esc(st.label)}</strong><em>${esc(st.hint)}</em></span>
            </label>
          </li>`).join("")}
      </ul>
      <button class="link-btn" data-quickadd="${esc(c.id)}">+ Add a task for ${esc(c.name)}</button>
    </section>`;
  }
  return html;
}

/* ---------------- pieces ---------------- */

function sortByDue(list) {
  return [...list].sort((a,b) => {
    if (!a.due && !b.due) return b.createdAt - a.createdAt;
    if (!a.due) return 1;
    if (!b.due) return -1;
    return a.due.localeCompare(b.due);
  });
}

function group(title, tasks, tone = "") {
  return `<section class="group">
    <header class="group-head"><h3 class="${tone}">${esc(title)}</h3><span class="count">${tasks.length}</span></header>
    <ul class="list">${sortByDue(tasks).map(taskRow).join("")}</ul>
  </section>`;
}

function taskRow(t) {
  const course = Store.get().courses.find(c => c.id === t.courseId);
  const overdue = t.due && !t.done && D.daysUntil(t.due) < 0;
  return `<li class="task ${t.done ? "is-done" : ""}">
    <button class="tick-btn" data-toggle="${esc(t.id)}" aria-label="${t.done ? "Mark incomplete" : "Mark complete"}">
      <span class="tick-circle" style="${course && !t.done ? `border-color:${esc(course.color)}` : ""}"></span>
    </button>
    <button class="task-body" data-edit="${esc(t.id)}">
      <span class="task-title">${t.flagged ? `<span class="flag" aria-label="Flagged">⚑</span> ` : ""}${esc(t.title)}</span>
      ${t.notes ? `<span class="task-notes">${esc(t.notes)}</span>` : ""}
      <span class="task-meta">
        ${course ? `<span class="chip" style="--c:${esc(course.color)}">${esc(course.name)}</span>` : ""}
        ${t.due ? `<span class="due ${overdue ? "is-overdue" : ""}">${esc(D.relative(t.due))}</span>` : ""}
        ${t.est ? `<span class="est">${esc(estLabel(t.est))}</span>` : ""}
      </span>
    </button>
  </li>`;
}

/* "Access 2" / "Access 2, Reference Help" — for blocks with no Access 1 hour. */
function rolesLabel(s) {
  const roles = [...new Set((s.segments || []).map(g => g.role))];
  return roles.join(", ") || s.label || "Shift";
}

function estLabel(m) {
  const n = Number(m);
  return n >= 240 ? "4 hrs+" : n >= 60 ? `${n/60} hr${n > 60 ? "s" : ""}` : `${n} min`;
}

function empty(title, body) {
  return `<div class="empty"><h3>${esc(title)}</h3><p>${esc(body)}</p></div>`;
}

function sweepProgress(wk) {
  const s = Store.get();
  const total = s.courses.length * CONFIG.SWEEP_STEPS.length;
  const marks = s.sweeps[wk] || {};
  let count = 0, coursesLeft = 0;
  for (const c of s.courses) {
    const mine = marks[c.id] || {};
    const hits = CONFIG.SWEEP_STEPS.filter(st => mine[st.id]).length;
    count += hits;
    if (hits < CONFIG.SWEEP_STEPS.length) coursesLeft++;
  }
  return { count, total, coursesLeft };
}

/* ---------------- sheets ---------------- */

function openSheet(id) {
  $("#scrim").hidden = false;
  const sheet = $(id);
  sheet.hidden = false;
  requestAnimationFrame(() => { $("#scrim").classList.add("is-on"); sheet.classList.add("is-on"); });
}

function closeSheets() {
  $("#scrim").classList.remove("is-on");
  $$(".sheet").forEach(s => s.classList.remove("is-on"));
  setTimeout(() => {
    $("#scrim").hidden = true;
    $$(".sheet").forEach(s => s.hidden = true);
  }, 260);
}

function openTaskSheet(task) {
  const courses = Store.get().courses;
  $("#task-course").innerHTML =
    `<option value="">None</option>` +
    courses.map(c => `<option value="${esc(c.id)}">${esc(c.name)}</option>`).join("");

  $("#task-id").value      = task?.id || "";
  $("#task-title").value   = task?.title || "";
  $("#task-notes").value   = task?.notes || "";
  $("#task-course").value  = task?.courseId || "";
  $("#task-due").value     = task?.due || "";
  $("#task-est").value     = task?.est || "";
  $("#task-flag").checked  = !!task?.flagged;

  $("#task-sheet-title").textContent = task?.id ? "Task" : "New Task";
  $("#task-save").textContent = task?.id ? "Save" : "Add";
  $("#task-delete").hidden = !task?.id;

  openSheet("#task-sheet");
  setTimeout(() => $("#task-title").focus(), 220);
}

function saveTaskSheet() {
  const title = $("#task-title").value.trim();
  if (!title) { $("#task-title").focus(); return; }

  const patch = {
    title,
    notes:    $("#task-notes").value.trim(),
    courseId: $("#task-course").value,
    due:      $("#task-due").value,
    est:      $("#task-est").value,
    flagged:  $("#task-flag").checked,
  };

  const id = $("#task-id").value;
  if (id) Store.updateTask(id, patch); else Store.addTask(patch);

  closeSheets();
  render();
}

/* ---------------- settings ---------------- */

function renderSettings() {
  const s = Store.get();
  const dayOpts = d => [0,1,2,3,4,5,6]
    .map(i => `<option value="${i}" ${i === d ? "selected" : ""}>${D.dayName(i)}</option>`).join("");

  $("#settings-body").innerHTML = `
    <section class="settings-block" id="settings-shifts">
      <h3>Shifts</h3>
      <p class="settings-note">A shift pings only for the reminders listed under it — add as many as you want, or remove them all to keep a shift silent. <strong>Access One</strong> marks which blocks contain Access 1 hours.</p>
      <ul class="shift-editor">
        ${s.shifts.map(sh => `
          <li class="shift-row ${sh.accessOne ? "is-access" : ""}">
            <select data-shift="${esc(sh.id)}" data-field="day">${dayOpts(sh.day)}</select>
            <input type="time" data-shift="${esc(sh.id)}" data-field="start" value="${esc(sh.start)}">
            <input type="time" data-shift="${esc(sh.id)}" data-field="end" value="${esc(sh.end)}">
            <label class="access-toggle">
              <input type="checkbox" class="switch" data-shift="${esc(sh.id)}" data-field="accessOne" ${sh.accessOne ? "checked" : ""}>
              <span>Access One</span>
            </label>
            <button class="row-remove" data-remove-shift="${esc(sh.id)}" aria-label="Remove shift">−</button>
            <ul class="reminder-list">
              ${Shifts.reminders(sh).map(t => `
                <li class="reminder-chip">
                  <span>Reminds ${esc(D.time(t))}</span>
                  <button data-drop-reminder="${esc(sh.id)}" data-time="${esc(t)}"
                          aria-label="Remove ${esc(D.time(t))} reminder">×</button>
                </li>`).join("") ||
                `<li class="reminder-none">No reminder — this shift stays silent.</li>`}
              <li class="reminder-add">
                <input type="time" id="new-reminder-${esc(sh.id)}" value="${esc(sh.start)}"
                       aria-label="New reminder time">
                <button class="link-btn" data-add-reminder="${esc(sh.id)}">Add reminder</button>
              </li>
            </ul>
          </li>`).join("") || `<li class="settings-empty">No shifts yet.</li>`}
      </ul>
      <button class="link-btn" id="add-shift">+ Add a shift</button>
    </section>

    <section class="settings-block">
      <h3>Courses</h3>
      <ul class="course-editor">
        ${s.courses.map(c => `
          <li class="course-row">
            <span class="dot" style="background:${esc(c.color)}"></span>
            <span>${esc(c.name)}</span>
            <button class="row-remove" data-remove-course="${esc(c.id)}" aria-label="Remove ${esc(c.name)}">−</button>
          </li>`).join("") || `<li class="settings-empty">No courses yet.</li>`}
      </ul>
      <form class="inline-add" id="add-course-form">
        <input id="new-course" placeholder="Add a course" maxlength="80">
        <button type="submit" class="link-btn">Add</button>
      </form>
    </section>

    <section class="settings-block">
      <h3>Reminders</h3>
      <label class="row"><span>Browser notification</span>
        <input type="checkbox" class="switch" id="set-notify" ${s.settings.notifications ? "checked" : ""}></label>
      <p class="settings-note">Fires at each reminder time above, but only while this tab is open. Your Google Calendar already emails and pings your phone at these times. To load them somewhere else:</p>
      <button class="btn-quiet" id="export-ics">Download calendar file (.ics)</button>
    </section>

    <section class="settings-block">
      <h3>Schedule</h3>
      <p class="settings-note">Paste a schedule to load it in one go — shifts, their hour-by-hour roles, and their reminders. Replaces your current shifts; leaves your tasks alone.</p>
      <textarea class="io-box" id="import-box" rows="3" placeholder='[{"id":"mon","day":1,"start":"15:00", ...}]' spellcheck="false"></textarea>
      <div class="io-actions">
        <button class="btn-quiet" id="import-shifts">Import schedule</button>
        <button class="link-btn" id="export-shifts">Copy mine out</button>
      </div>
      <p class="settings-note" id="io-status" hidden></p>
    </section>

    <section class="settings-block">
      <h3>Data</h3>
      <p class="settings-note">Everything lives in this browser only — nothing is uploaded anywhere, and none of it is in the app's code.</p>
      <button class="destructive" id="reset-all">Reset Everything</button>
    </section>

    <p class="colophon">Sweep · ${esc(s.tasks.length)} tasks · ${esc(Object.keys(s.sweeps).length)} weeks swept</p>`;
}

/* Build an .ics with a weekly recurring event per Access One shift.
 * Gives you real phone alerts without the app being open. */
function exportICS() {
  const shifts = Shifts.reminding();
  if (!shifts.length) { alert("Add a reminder to at least one shift first."); return; }

  const pad = n => String(n).padStart(2, "0");
  const DAYS = ["SU","MO","TU","WE","TH","FR","SA"];
  const stamp = new Date().toISOString().replace(/[-:]|\.\d{3}/g, "");
  const lines = [
    "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Sweep//Access One//EN",
    "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
  ];

  shifts.forEach((s, i) => {
    // First occurrence: the next time this weekday comes around.
    const base = new Date();
    base.setDate(base.getDate() + ((s.day - base.getDay() + 7) % 7));
    const [sh, sm] = s.start.split(":").map(Number);
    const [eh, em] = s.end.split(":").map(Number);
    const fmt = (h, m) =>
      `${base.getFullYear()}${pad(base.getMonth()+1)}${pad(base.getDate())}T${pad(h)}${pad(m)}00`;

    // One alarm per reminder on the block, offset from the block's start.
    const offsets = Shifts.reminders(s)
      .map(t => Math.max(0, D.toMinutes(t) - (sh * 60 + sm)));
    const summary = Shifts.accessOneSummary(s);

    lines.push(
      "BEGIN:VEVENT",
      `UID:sweep-access-one-${i}-${stamp}@sweep.local`,
      `DTSTAMP:${stamp}`,
      `DTSTART:${fmt(sh, sm)}`,
      `DTEND:${fmt(eh, em)}`,
      `RRULE:FREQ=WEEKLY;BYDAY=${DAYS[s.day]}`,
      "SUMMARY:Access One — sweep Canvas",
      `DESCRIPTION:First thing this shift: go through Canvas course by course and pull out everything due this week.${summary ? " (" + summary + ")" : ""}`,
      ...offsets.flatMap(o => [
        "BEGIN:VALARM", `TRIGGER:PT${o}M`, "ACTION:DISPLAY",
        "DESCRIPTION:Access One — start with Canvas", "END:VALARM",
      ]),
      "END:VEVENT",
    );
  });

  lines.push("END:VCALENDAR");
  const blob = new Blob([lines.join("\r\n")], { type: "text/calendar" });
  const a = Object.assign(document.createElement("a"),
    { href: URL.createObjectURL(blob), download: "access-one.ics" });
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

function ioStatus(msg, bad = false) {
  const el = document.getElementById("io-status");
  if (!el) return;
  el.hidden = false;
  el.textContent = msg;
  el.style.color = bad ? "var(--danger)" : "var(--accent)";
}

/* Load a schedule pasted in as JSON. Validated rather than trusted — a bad paste
 * should say what's wrong, not quietly leave you with no reminders. */
function importShifts() {
  const raw = document.getElementById("import-box").value.trim();
  if (!raw) { ioStatus("Nothing pasted yet.", true); return; }

  let parsed;
  try { parsed = JSON.parse(raw); }
  catch (e) { ioStatus("That isn't valid JSON — check for a missing bracket or quote.", true); return; }

  if (!Array.isArray(parsed)) { ioStatus("Expected a list of shifts, starting with [.", true); return; }

  const time = v => typeof v === "string" && /^([01]\d|2[0-3]):[0-5]\d$/.test(v);
  const clean = [];

  for (const sh of parsed) {
    if (!sh || typeof sh !== "object") { ioStatus("One entry isn't a shift object.", true); return; }
    if (!Number.isInteger(sh.day) || sh.day < 0 || sh.day > 6) { ioStatus('Every shift needs a "day" from 0 to 6 (0 = Sunday).', true); return; }
    if (!time(sh.start) || !time(sh.end)) { ioStatus('"start" and "end" must look like "15:00".', true); return; }

    const reminders = (Array.isArray(sh.reminders) ? sh.reminders : []).filter(time);
    const segments = (Array.isArray(sh.segments) ? sh.segments : [])
      .filter(g => g && time(g.start) && time(g.end) && typeof g.role === "string")
      .map(g => ({ start: g.start, end: g.end, role: g.role }));

    clean.push({
      id: typeof sh.id === "string" && sh.id ? sh.id : Math.random().toString(36).slice(2, 10),
      day: sh.day, start: sh.start, end: sh.end,
      accessOne: !!sh.accessOne,
      label: typeof sh.label === "string" ? sh.label : "",
      reminders: [...new Set(reminders)].sort(),
      segments,
    });
  }

  Store.replaceShifts(clean);
  renderSettings(); render();
  const pings = clean.reduce((n, s) => n + s.reminders.length, 0);
  ioStatus(`Loaded ${clean.length} shift${clean.length === 1 ? "" : "s"} and ${pings} reminder${pings === 1 ? "" : "s"}.`);
}

/* ---------------- notifications ---------------- */

let lastNotified = "";

function checkNotify() {
  const s = Store.get();
  if (!s.settings.notifications) return;
  if (!("Notification" in window) || Notification.permission !== "granted") return;

  const cur = Shifts.current();
  if (!cur) return;

  const due = Shifts.dueReminder(cur);
  if (!due) return;

  // Keyed per reminder per day: each reminder you've added fires once, and a
  // mid-shift reload never re-fires one that already went out.
  const key = `${D.iso(D.today())}|${cur.id}|${due}`;
  if (lastNotified === key || sessionStorage.getItem("sweep.notified") === key) return;

  lastNotified = key;
  try { sessionStorage.setItem("sweep.notified", key); } catch (e) { /* private mode */ }
  new Notification("Access One — start with Canvas", {
    body: "Go course by course and pull out everything due this week.",
    tag: "sweep-access-one",
  });
}

/* ---------------- events ---------------- */

function bindChrome() {
  $$(".seg").forEach(b => b.addEventListener("click", () => {
    view = b.dataset.view; renderSegmented(); renderView();
  }));

  $("#add-btn").addEventListener("click", () => openTaskSheet(null));
  $("#task-save").addEventListener("click", saveTaskSheet);
  $("#task-form").addEventListener("submit", e => { e.preventDefault(); saveTaskSheet(); });

  $("#task-delete").addEventListener("click", () => {
    const id = $("#task-id").value;
    if (id && confirm("Delete this task?")) { Store.removeTask(id); closeSheets(); render(); }
  });

  $("#settings-btn").addEventListener("click", () => { renderSettings(); openSheet("#settings-sheet"); });
  $("#scrim").addEventListener("click", closeSheets);
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeSheets(); });
  $$("[data-close]").forEach(b => b.addEventListener("click", closeSheets));

  document.addEventListener("click", onClick);
  document.addEventListener("change", onChange);

  setInterval(checkNotify, 60_000);
  checkNotify();
}

function onClick(e) {
  const t = e.target.closest("[data-toggle],[data-edit],[data-goto],[data-dismiss],[data-quickadd],[data-open-settings],#clear-done,#add-shift,#reset-all,#export-ics,#import-shifts,#export-shifts,[data-remove-shift],[data-remove-course],[data-add-reminder],[data-drop-reminder]");
  if (!t) return;

  if (t.dataset.toggle)  { Store.toggleTask(t.dataset.toggle); render(); return; }
  if (t.dataset.edit)    { openTaskSheet(Store.get().tasks.find(x => x.id === t.dataset.edit)); return; }
  if (t.dataset.goto)    { view = t.dataset.goto; renderSegmented(); renderView(); return; }
  if (t.dataset.dismiss) { Store.dismiss(t.dataset.dismiss); renderBanner(); return; }

  if (t.dataset.quickadd) { openTaskSheet({ courseId: t.dataset.quickadd }); return; }

  if (t.dataset.openSettings) { renderSettings(); openSheet("#settings-sheet"); return; }

  if (t.id === "clear-done") { Store.clearCompleted(); render(); return; }

  if (t.id === "add-shift") { Store.addShift({}); renderSettings(); render(); return; }
  if (t.dataset.removeShift)  { Store.removeShift(t.dataset.removeShift); renderSettings(); render(); return; }
  if (t.dataset.removeCourse) { Store.removeCourse(t.dataset.removeCourse); renderSettings(); render(); return; }

  if (t.dataset.addReminder) {
    const input = document.getElementById(`new-reminder-${t.dataset.addReminder}`);
    if (input && input.value) { Store.addReminder(t.dataset.addReminder, input.value); renderSettings(); render(); }
    return;
  }
  if (t.dataset.dropReminder) {
    Store.removeReminder(t.dataset.dropReminder, t.dataset.time);
    renderSettings(); render(); return;
  }

  if (t.id === "import-shifts") { importShifts(); return; }
  if (t.id === "export-shifts") {
    const box = document.getElementById("import-box");
    const shifts = Store.get().shifts;
    box.value = JSON.stringify(shifts);
    box.select();
    ioStatus(`${shifts.length} shift${shifts.length === 1 ? "" : "s"} written out — copy it somewhere safe.`);
    return;
  }

  if (t.id === "export-ics") { exportICS(); return; }

  if (t.id === "reset-all") {
    if (confirm("Erase all tasks, courses, shifts and sweep history from this browser?")) {
      Store.reset(); closeSheets(); render();
    }
  }
}

function onChange(e) {
  const el = e.target;

  if (el.dataset.sweep) {
    Store.setSweepStep(D.weekKey(), el.dataset.sweep, el.dataset.step, el.checked);
    renderView(); renderBanner(); return;
  }

  if (el.dataset.shift) {
    const field = el.dataset.field;
    const value = field === "accessOne" ? el.checked : (field === "day" ? Number(el.value) : el.value);
    Store.updateShift(el.dataset.shift, { [field]: value });
    // Deliberately not re-rendering the settings pane: rebuilding the inputs
    // would tear the field out from under you mid-edit. Just restyle the row.
    const row = el.closest(".shift-row");
    if (row) row.classList.toggle("is-access", !!Store.get().shifts.find(x => x.id === el.dataset.shift)?.accessOne);
    render(); return;
  }

  if (el.id === "set-notify") {
    if (el.checked && "Notification" in window && Notification.permission !== "granted") {
      Notification.requestPermission().then(p => {
        Store.setSetting("notifications", p === "granted");
        renderSettings();
      });
    } else {
      Store.setSetting("notifications", el.checked);
    }
  }
}

document.addEventListener("submit", e => {
  if (e.target.id !== "add-course-form") return;
  e.preventDefault();
  const input = $("#new-course");
  if (input.value.trim()) { Store.addCourse(input.value); input.value = ""; renderSettings(); render(); }
});

boot();
