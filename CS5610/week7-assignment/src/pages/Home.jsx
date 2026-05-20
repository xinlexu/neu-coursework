export default function Home() {
  console.log("HOME_LOADED", new Date().toISOString(), import.meta.url);
  return (
    <section>
      <h2>Home</h2>

      <div className="hero">
        <img
          src="/image.png"
          alt="Week 7 assignment screenshot"
          className="screenshot"
        />
      </div>

      <p>Use the tabs above to switch between subpages under <code>/</code>.</p>
      <ul>
        <li><strong>Counter</strong>  demonstrates <code>useState</code>.</li>
        <li><strong>Clock</strong>  demonstrates <code>useEffect</code>.</li>
      </ul>
    </section>
  );
}
