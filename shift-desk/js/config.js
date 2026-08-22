/* Sweep — configuration
 *
 * Everything here is a *default*. Once you use the app, your real data lives in
 * your browser (localStorage) and the app stops reading these values. To reset
 * back to these defaults: Settings -> Reset Everything.
 *
 * Edit this file to change what a brand-new install starts with.
 */

const CONFIG = {

  /* Your courses. Colors are the accent dot beside each task. */
  COURSES: [
    { id: "statics",    name: "Statics",                             color: "#0a84ff" },
    { id: "ochem",      name: "Organic Chemistry I",                 color: "#ff9f0a" },
    { id: "ochem-lab",  name: "Organic Chemistry I Lab",             color: "#ffd60a" },
    { id: "matsci",     name: "Principles of Materials Science",     color: "#30d158" },
    { id: "matsci-lab", name: "Principles of Materials Science Lab", color: "#64d2ff" },
  ],

  /* Your shifts.
   *
   * Deliberately empty: this file is public, and a shift schedule says exactly
   * where a named person is every week. Your real schedule lives only in your
   * browser — load it once via Settings -> Import schedule, and it stays on your
   * device from then on.
   *
   * A shift is a *block* — the whole stretch you're at the desk. Inside it, each
   * hour carries a role. Only the times in `reminders` ever ping you.
   *
   *   day       0=Sun 1=Mon 2=Tue 3=Wed 4=Thu 5=Fri 6=Sat
   *   accessOne does this block contain any Access 1 hour?
   *   reminders times this block pings, as "HH:MM". Empty = never pings.
   *   segments  hour-by-hour roles, shown in the app for context.
   *
   * Shape, for reference:
   *
   *   { id: "example", day: 4, start: "09:00", end: "11:00",
   *     accessOne: true, reminders: ["09:00"],
   *     segments: [{ start: "09:00", end: "10:00", role: "Access 1" }] }
   */
  SHIFTS: [],

  /* The guided sweep. One pass per course, per week. Reorder or reword freely. */
  SWEEP_STEPS: [
    { id: "announce", label: "Announcements",       hint: "Anything new posted since last week?" },
    { id: "assign",   label: "Assignments",         hint: "Everything due in the next 7 days." },
    { id: "modules",  label: "This week's module",  hint: "Readings, problem sets, pre-labs." },
    { id: "grades",   label: "Grades",              hint: "Missing scores or feedback to act on." },
  ],

  /* Where the sweep sends you. */
  CANVAS_URL: "https://georgefox.instructure.com",

  SETTINGS: {
    weekStartsOn: 1,        // 1 = Monday
    notifications: false,   // asked for the first time you enable it
    remindAt: "start",
  },
};
