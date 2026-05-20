import { useState } from "react";

export default function Counter() {
  const [count, setCount] = useState(0);

  return (
    <section>
      <h2>Counter (useState)</h2>
      <p>Current count: <strong>{count}</strong></p>
      <div className="btn-row">
        <button onClick={() => setCount(c => c - 1)} aria-label="decrement">-1</button>
        <button onClick={() => setCount(0)} aria-label="reset">Reset</button>
        <button onClick={() => setCount(c => c + 1)} aria-label="increment">+1</button>
      </div>
    </section>
  );
}