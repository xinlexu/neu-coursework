import React, { useEffect, useState } from "react";
import { apiGet, apiPost, apiPatch, apiDelete } from "../api/client";

const PRIORITIES = ["high", "medium", "low"];

export default function Home() {
  const [items, setItems] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const [q, setQ] = useState("");
  const [status, setStatus] = useState("all");
  const [priority, setPriority] = useState("all");
  const [tag, setTag] = useState("");

  const [title, setTitle] = useState("");
  const [newPriority, setNewPriority] = useState("medium");
  const [tagsInput, setTagsInput] = useState("");

  useEffect(() => { ping(); load(); }, []);
  useEffect(() => { load(); }, [q, status, priority, tag]);

  async function ping() {
    try {
      const d = await apiGet("/api/hello/");
      setBadge(d?.status === "running" ? "running" : "offline");
    } catch {
      setBadge("offline");
    }
  }

  async function load() {
    setLoading(true); setErr("");
    try {
      const params = new URLSearchParams();
      if (q.trim()) params.set("q", q.trim());
      if (status !== "all") params.set("status", status);
      if (priority !== "all") params.set("priority", priority);
      if (tag.trim()) params.set("tag", tag.trim());
      const [list, s] = await Promise.all([
        apiGet(`/api/todos/?${params.toString()}`),
        apiGet("/api/todos/stats/"),
      ]);
      setItems(list.items || []);
      setStats(s);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function addTodo(e) {
    e.preventDefault();
    if (!title.trim()) return;
    await apiPost("/api/todos/", { title: title.trim(), priority: newPriority, tags: tagsInput });
    setTitle(""); setNewPriority("medium"); setTagsInput("");
    await load();
  }

  async function toggleDone(it) {
    await apiPatch(`/api/todos/${it.id}/`, { done: !it.done });
    await load();
  }

  async function remove(it) {
    await apiDelete(`/api/todos/${it.id}/`);
    await load();
  }

  const [badge, setBadge] = useState("checking");
  const empty = !loading && items.length === 0;

  return (
    <div>
      <div className="header">
        <h1>Student's Todo List</h1>
        <span className="badge">
          Backend: {badge === "checking" ? "checking…" : badge === "running" ? "running" : "offline"}
        </span>
      </div>

      <section>
        <h2>Stats</h2>
        {!stats ? <p>…</p> : (
          <div style={{display:"flex", gap:16, flexWrap:"wrap"}}>
            <Stat label="total" value={stats.total} />
            <Stat label="active" value={stats.active} />
            <Stat label="done" value={stats.done} />
            <Stat label="high" value={stats.by_priority?.high ?? 0} />
            <Stat label="medium" value={stats.by_priority?.medium ?? 0} />
            <Stat label="low" value={stats.by_priority?.low ?? 0} />
          </div>
        )}
      </section>

      <section>
        <h2>Tasks</h2>
        <div className="toolbar">
          <input placeholder="Search tasks…" value={q} onChange={e=>setQ(e.target.value)} />
          <select value={status} onChange={e=>setStatus(e.target.value)}>
            <option value="all">all</option>
            <option value="active">active</option>
            <option value="done">done</option>
          </select>
          <select value={priority} onChange={e=>setPriority(e.target.value)}>
            <option value="all">all priorities</option>
            {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
          <input placeholder="Filter by tag" value={tag} onChange={e=>setTag(e.target.value)} />
        </div>

        {loading && <p>Loading…</p>}
        {err && <p className="error">{err}</p>}
        {empty && <p>No tasks.</p>}

        <ul style={{listStyle:"none", padding:0, margin:0}}>
          {items.map(it => (
            <li key={it.id} className="card">
              <input type="checkbox" checked={it.done} onChange={()=>toggleDone(it)} />
              <div>
                <div style={{fontWeight:600, textDecoration: it.done ? "line-through" : "none"}}>{it.title}</div>
                <div style={{fontSize:12, opacity:.8}}>priority: {it.priority}{it.tags?.length ? <> · tags: {it.tags.join(", ")}</> : null}</div>
              </div>
              <button onClick={()=>remove(it)}>Delete</button>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Add a task</h2>
        <form onSubmit={addTodo}>
          <div style={{display:"grid", gap:10, gridTemplateColumns:"1fr 160px 1fr auto"}}>
            <input placeholder="Task title" value={title} onChange={e => setTitle(e.target.value)} required />
            <select value={newPriority} onChange={e => setNewPriority(e.target.value)}>
              {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
            <input placeholder="Tags (comma-separated)" value={tagsInput} onChange={e => setTagsInput(e.target.value)} />
            <button type="submit">Add</button>
          </div>
          <div className="helper">Example: tags "school,urgent"</div>
        </form>
      </section>
    </div>
  );
}

function Stat({label, value}) {
  return (
    <div className="stat">
      <div style={{fontSize:12, opacity:.8}}>{label}</div>
      <div style={{fontSize:20, fontWeight:700}}>{value}</div>
    </div>
  );
}
