import React, { useState } from "react";
import { apiPost } from "../api/client";

export default function Contact() {
  const [name, setName] = useState("");
  const [message, setMessage] = useState("");
  const [sent, setSent] = useState(false);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setLoading(true); setErr(""); setSent(false);
    try {
      await apiPost("/api/feedback/", { name, message });
      setSent(true);
      setMessage("");
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1>Contact</h1>
      <section>
        <form onSubmit={submit} style={{display:"grid", gap:12}}>
          <input placeholder="Your name (optional)" value={name} onChange={e=>setName(e.target.value)} />
          <textarea
            placeholder="Your message"
            value={message}
            onChange={e=>setMessage(e.target.value)}
            rows={5}
            style={{resize:"vertical"}}
            required
          />
          <div>
            <button type="submit" disabled={loading}>{loading ? "Sending…" : "Send"}</button>
          </div>
          {sent && <div className="success">Message sent.</div>}
          {err && <p className="error">{err}</p>}
        </form>
      </section>
    </div>
  );
}
