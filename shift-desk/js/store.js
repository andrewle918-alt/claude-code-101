/* Sweep — state, persistence, and date helpers.
 * No dependencies. Everything is kept in localStorage under one key. */

const KEY = "sweep.v1";

const Store = (() => {
  let state = load();

  function seed() {
    return {
      version: 1,
      courses: CONFIG.COURSES.map(c => ({ ...c })),
      shifts:  CONFIG.SHIFTS.map(s => ({ ...s })),
      tasks:   [],
      sweeps:  {},                 // { "2026-W35": { statics: {announce:true,...}, ... } }
      settings:{ ...CONFIG.SETTINGS },
      dismissed: {},               // { "2026-W35|mon": true } — banner dismissals
    };
  }

  function load() {
    try {
      const raw = localStorage.getItem(KEY);
      if (!raw) return seed();
      const parsed = JSON.parse(raw);
      const base = seed();
      const merged = { ...base, ...parsed, settings: { ...base.settings, ...(parsed.settings || {}) } };
      // Saved data from before shifts carried a list of reminders.
      merged.shifts = (merged.shifts || []).map(sh => {
        if (Array.isArray(sh.reminders)) return sh;
        const at = sh.remindAt || (sh.accessOne ? sh.start : "");
        const { remindAt, ...rest } = sh;
        return { ...rest, reminders: at ? [at] : [] };
      });
      return merged;
    } catch (e) {
      console.warn("Sweep: could not read saved data, starting fresh.", e);
      return seed();
    }
  }

  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); }
    catch (e) { console.warn("Sweep: could not save.", e); }
  }

  const uid = () => Math.random().toString(36).slice(2, 10);

  return {
    get: () => state,
    save,
    reset() { state = seed(); save(); },

    /* ---- tasks ---- */
    addTask(t) {
      state.tasks.push({
        id: uid(), title: "", notes: "", courseId: "", due: "", est: "",
        flagged: false, done: false, createdAt: Date.now(), doneAt: null, ...t,
      });
      save();
    },
    updateTask(id, patch) {
      const t = state.tasks.find(x => x.id === id);
      if (!t) return;
      Object.assign(t, patch);
      save();
    },
    toggleTask(id) {
      const t = state.tasks.find(x => x.id === id);
      if (!t) return;
      t.done = !t.done;
      t.doneAt = t.done ? Date.now() : null;
      save();
    },
    removeTask(id) {
      state.tasks = state.tasks.filter(x => x.id !== id);
      save();
    },
    clearCompleted() {
      state.tasks = state.tasks.filter(t => !t.done);
      save();
    },

    /* ---- courses ---- */
    addCourse(name) {
      const palette = ["#0a84ff","#ff9f0a","#ffd60a","#30d158","#64d2ff","#bf5af2","#ff453a","#ac8e68"];
      state.courses.push({
        id: uid(),
        name: name.trim(),
        color: palette[state.courses.length % palette.length],
      });
      save();
    },
    removeCourse(id) {
      state.courses = state.courses.filter(c => c.id !== id);
      state.tasks.forEach(t => { if (t.courseId === id) t.courseId = ""; });
      save();
    },

    /* ---- shifts ---- */
    addShift(s) {
      state.shifts.push({ id: uid(), day: 1, start: "09:00", end: "11:00", accessOne: false,
                          reminders: [], segments: [], label: "", ...s });
      save();
    },
    updateShift(id, patch) {
      const s = state.shifts.find(x => x.id === id);
      if (s) { Object.assign(s, patch); save(); }
    },
    removeShift(id) {
      state.shifts = state.shifts.filter(x => x.id !== id);
      save();
    },

    replaceShifts(list) { state.shifts = list; save(); },

    /* Reminders are per shift and freely editable — add as many as you want,
     * or strip a shift back to none. */
    addReminder(shiftId, time) {
      const s = state.shifts.find(x => x.id === shiftId);
      if (!s || !time) return;
      s.reminders = s.reminders || [];
      if (!s.reminders.includes(time)) {
        s.reminders.push(time);
        s.reminders.sort();
        save();
      }
    },
    removeReminder(shiftId, time) {
      const s = state.shifts.find(x => x.id === shiftId);
      if (!s) return;
      s.reminders = (s.reminders || []).filter(t => t !== time);
      save();
    },

    /* ---- sweep ---- */
    sweepFor(weekKey) {
      if (!state.sweeps[weekKey]) { state.sweeps[weekKey] = {}; save(); }
      return state.sweeps[weekKey];
    },
    setSweepStep(weekKey, courseId, stepId, value) {
      const wk = this.sweepFor(weekKey);
      if (!wk[courseId]) wk[courseId] = {};
      wk[courseId][stepId] = value;
      save();
    },

    setSetting(k, v) { state.settings[k] = v; save(); },
    dismiss(key)     { state.dismissed[key] = true; save(); },
  };
})();


/* ---------- dates ---------- */

const D = {
  today() { const d = new Date(); d.setHours(0,0,0,0); return d; },

  iso(d) {
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
  },

  parse(isoStr) {
    if (!isoStr) return null;
    const [y,m,dd] = isoStr.split("-").map(Number);
    return new Date(y, m-1, dd);
  },

  /* ISO-8601 week key, e.g. "2026-W35". Weeks roll over Monday. */
  weekKey(d = new Date()) {
    const t = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    t.setDate(t.getDate() + 4 - (t.getDay() || 7));
    const yearStart = new Date(t.getFullYear(), 0, 1);
    const week = Math.ceil(((t - yearStart) / 86400000 + 1) / 7);
    return `${t.getFullYear()}-W${String(week).padStart(2,"0")}`;
  },

  startOfWeek(d = new Date()) {
    const s = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const shift = (s.getDay() - CONFIG.SETTINGS.weekStartsOn + 7) % 7;
    s.setDate(s.getDate() - shift);
    return s;
  },

  addDays(d, n) { const x = new Date(d); x.setDate(x.getDate() + n); return x; },

  daysUntil(isoStr) {
    const d = D.parse(isoStr);
    if (!d) return null;
    return Math.round((d - D.today()) / 86400000);
  },

  /* "Today", "Tomorrow", "3 days ago", "Fri", "Oct 14" */
  relative(isoStr) {
    const n = D.daysUntil(isoStr);
    if (n === null) return "";
    if (n === 0) return "Today";
    if (n === 1) return "Tomorrow";
    if (n === -1) return "Yesterday";
    if (n < -1) return `${Math.abs(n)} days ago`;
    if (n < 7) return D.parse(isoStr).toLocaleDateString(undefined, { weekday: "long" });
    return D.parse(isoStr).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  },

  time(hhmm) {
    const [h, m] = hhmm.split(":").map(Number);
    const d = new Date(); d.setHours(h, m, 0, 0);
    return d.toLocaleTimeString(undefined, { hour: "numeric", minute: m ? "2-digit" : undefined });
  },

  minutesNow() { const d = new Date(); return d.getHours()*60 + d.getMinutes(); },
  toMinutes(hhmm) { const [h,m] = hhmm.split(":").map(Number); return h*60 + m; },

  dayName(i) { return ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"][i]; },
};


/* ---------- shift logic ----------
 * The one rule that matters: only shifts with accessOne === true ever remind you. */

const Shifts = {
  accessOne() { return Store.get().shifts.filter(s => s.accessOne); },

  /* Every reminder time on a block, earliest first. */
  reminders(s) { return [...(s.reminders || [])].sort(); },

  /* Any shift carrying at least one reminder — Access One or not. */
  reminding() { return Store.get().shifts.filter(s => this.reminders(s).length); },

  /* The Access 1 hours inside a block — what makes it worth reminding about. */
  accessOneHours(s) {
    return (s.segments || []).filter(g => g.role === "Access 1");
  },

  /* The Access One block happening right now, if any. Because this matches the
   * whole block rather than each Access 1 hour, a block whose Access 1 hours are
   * split across it is still one shift, not two. */
  current() {
    const now = D.minutesNow(), day = new Date().getDay();
    return this.reminding().find(s =>
      s.day === day && now >= D.toMinutes(s.start) && now < D.toMinutes(s.end)) || null;
  },

  /* The reminder on this block that is due right now, if any. Returns the time
   * string so the caller can key a notification per reminder, not per block —
   * two reminders on one shift each fire once, and neither re-fires on reload. */
  dueReminder(s, windowMins = 10) {
    const now = D.minutesNow();
    return this.reminders(s).find(t => {
      const at = D.toMinutes(t);
      return now >= at && now - at <= windowMins;
    }) || null;
  },

  /* The next Access One block within the next 7 days. */
  next() {
    const now = D.minutesNow(), today = new Date().getDay();
    let best = null;
    for (const s of this.reminding()) {
      for (let offset = 0; offset < 8; offset++) {
        const day = (today + offset) % 7;
        if (s.day !== day) continue;
        if (offset === 0 && D.toMinutes(s.start) <= now) continue;
        const mins = offset * 1440 + D.toMinutes(s.start) - now;
        if (!best || mins < best.mins) best = { shift: s, mins, offset };
        break;
      }
    }
    return best;
  },

  /* Every shift on a given weekday, Access One or not. */
  onDay(day) {
    return Store.get().shifts
      .filter(s => s.day === day)
      .sort((a,b) => D.toMinutes(a.start) - D.toMinutes(b.start));
  },

  /* "Access 1 at 12 PM and 2 PM" — the hours that earned the reminder. */
  accessOneSummary(s) {
    const hours = this.accessOneHours(s).map(g => D.time(g.start));
    if (!hours.length) return "";
    if (hours.length === 1) return `Access 1 at ${hours[0]}`;
    return `Access 1 at ${hours.slice(0, -1).join(", ")} and ${hours[hours.length - 1]}`;
  },

  countdown(mins) {
    if (mins < 60) return `in ${mins} min`;
    if (mins < 1440) {
      const h = Math.round(mins/60);
      return `in ${h} hour${h === 1 ? "" : "s"}`;
    }
    const d = Math.floor(mins/1440);
    return d === 1 ? "tomorrow" : `in ${d} days`;
  },
};
