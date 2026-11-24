import React, { useState } from 'react';

const storageKey = 'agrismart:smart-diary:v1';
const activities = ['Sowing', 'Irrigation', 'Fertilizer', 'Crop observation', 'Harvest', 'Other'];

function today() {
  const now = new Date();
  return [now.getFullYear(), now.getMonth() + 1, now.getDate()]
    .map(value => String(value).padStart(2, '0')).join('-');
}

function readDiary() {
  try {
    const entries = JSON.parse(localStorage.getItem(storageKey));
    return Array.isArray(entries) ? entries : [];
  } catch {
    return [];
  }
}

export default function SmartFarmDiary() {
  const [entries, setEntries] = useState(readDiary);
  const [fieldFilter, setFieldFilter] = useState('');
  const [error, setError] = useState('');
  const fields = [...new Set(entries.map(entry => entry.field))].sort();
  const visible = entries.filter(entry => !fieldFilter || entry.field === fieldFilter);
  const date = today();
  const pending = visible.filter(entry => entry.plan && !entry.done)
    .sort((a, b) => a.date.localeCompare(b.date));
  const history = visible.filter(entry => !entry.plan || entry.done)
    .sort((a, b) => (b.completedDate || b.date).localeCompare(a.completedDate || a.date));
  const overdue = pending.filter(entry => entry.date < date).length;
  const dueToday = pending.filter(entry => entry.date === date).length;

  function save(next) {
    try {
      localStorage.setItem(storageKey, JSON.stringify(next));
      setEntries(next);
      setError('');
      return true;
    } catch {
      setError('This browser could not save your diary. Check that local storage is enabled.');
      return false;
    }
  }

  function add(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const field = data.get('field').trim();
    if (!field) {
      setError('Enter a field or plot name.');
      return;
    }
    const entry = {
      id: crypto.randomUUID(),
      field,
      crop: data.get('crop').trim(),
      date: data.get('date'),
      activity: data.get('activity'),
      notes: data.get('notes').trim(),
      plan: data.get('kind') === 'plan',
    };
    if (save([entry, ...entries])) {
      setFieldFilter(field);
      form.reset();
    }
  }

  function renderEntry(entry) {
    return (
      <li key={entry.id} className="diary-entry">
        <div>
          <b>{entry.activity} · {entry.field}{entry.crop && ' · ' + entry.crop}</b>
          <small>{entry.completedDate ? 'Done ' + entry.completedDate + ' · Planned ' : ''}{entry.date}</small>
          {entry.notes && <p>{entry.notes}</p>}
        </div>
        {entry.plan && !entry.done &&
          <button type="button" onClick={() => save(entries.map(item =>
            item.id === entry.id ? { ...item, done: true, completedDate: today() } : item
          ))}>Mark done</button>}
      </li>
    );
  }

  return (
    <section aria-labelledby="diary-title">
      <div className="heading">
        <span className="eyebrow">FIELD PLANNER</span>
        <h2 id="diary-title">Smart Farm Diary</h2>
        <p>Plan field work and keep a dated history of what you did and observed.</p>
        <small>Diary entries are saved in this browser. Due reminders appear here when you open the diary.</small>
      </div>
      {error && <p className="error" role="alert">{error}</p>}
      <form className="panel" onSubmit={add}>
        <h3>Add a diary entry</h3>
        <div className="fields">
          <label>Field or plot<input name="field" required maxLength={80} list="diary-fields" defaultValue={fieldFilter}/></label>
          <datalist id="diary-fields">{fields.map(field => <option key={field} value={field}/>)}</datalist>
          <label>Crop<input name="crop" maxLength={80} placeholder="Optional"/></label>
          <label>Activity<select name="activity">
            {activities.map(activity => <option key={activity}>{activity}</option>)}
          </select></label>
          <label>Date<input name="date" type="date" required defaultValue={date}/></label>
          <label>Entry type<select name="kind">
            <option value="log">Record completed work or observation</option>
            <option value="plan">Plan a task</option>
          </select></label>
        </div>
        <label>Notes<textarea name="notes" maxLength={1000} rows={3} placeholder="What did you do, notice or plan?"/></label>
        <button className="primary">Save diary entry</button>
      </form>
      <section className="panel">
        <label>Show field<select value={fieldFilter} onChange={event => setFieldFilter(event.target.value)}>
          <option value="">All fields</option>
          {fields.map(field => <option key={field}>{field}</option>)}
        </select></label>
        <div className="diary-summary">
          <span><b>{overdue}</b> overdue</span>
          <span><b>{dueToday}</b> due today</span>
          <span><b>{pending.length - overdue - dueToday}</b> upcoming</span>
        </div>
        <h3>Planned work</h3>
        {pending.length ? <ul className="diary-list">{pending.map(renderEntry)}</ul> : <p>No planned tasks.</p>}
        <h3>Field history</h3>
        {history.length ? <ul className="diary-list">{history.map(renderEntry)}</ul> : <p>No completed work or observations yet.</p>}
      </section>
    </section>
  );
}
