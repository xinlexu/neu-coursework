import React, { useEffect, useState } from "react";
import { apiGet } from "../api/client";

export default function About() {
  const [meta, setMeta] = useState(null);
  useEffect(() => { apiGet("/api/meta/").then(setMeta).catch(()=>{}); }, []);
  return (
    <div>
      <h1>About</h1>
      <section>
        <p>React frontend with a Django API at <code>/api/*</code>. See the README in the repo for details.</p>
        {meta && <p style={{opacity:.8}}>Backend: <code>{meta.service}</code> · {meta.now}</p>}
      </section>
    </div>
  );
}
