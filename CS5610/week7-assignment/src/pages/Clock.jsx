import { useEffect, useState } from "react";

export default function Clock() {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <section>
      <h2>Clock (useEffect)</h2>
      <p>The current time is:</p>
      <p className="time">{now.toLocaleString()}</p>
    </section>
  );
}