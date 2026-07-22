const upcomingSteps = [
  "Model danych i migracje",
  "API danych planistycznych",
  "Solver CP-SAT",
  "Widok harmonogramu",
];

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="overview">
        <div>
          <p className="eyebrow">CrewPlan Lite</p>
          <h1>Planowanie ekip infrastrukturalnych</h1>
          <p className="lead">
            Minimalny szkielet aplikacji jest gotowy. Kolejne etapy dodadzą
            model domenowy, dane demo, solver oraz widok harmonogramu.
          </p>
        </div>
      </section>

      <section className="status-grid" aria-label="Status projektu">
        <article>
          <span>Backend</span>
          <strong>FastAPI /health</strong>
          <p>API wystawia pierwszy endpoint kontrolny.</p>
        </article>
        <article>
          <span>Frontend</span>
          <strong>Next.js App Router</strong>
          <p>Aplikacja webowa ma bazowy layout i stronę startową.</p>
        </article>
        <article>
          <span>Infrastruktura</span>
          <strong>PostgreSQL</strong>
          <p>Baza lokalna startuje przez Docker Compose.</p>
        </article>
      </section>

      <section className="next-steps" aria-label="Kolejne etapy">
        <h2>Kolejne etapy</h2>
        <ol>
          {upcomingSteps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </section>
    </main>
  );
}
