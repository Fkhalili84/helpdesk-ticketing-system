import { useEffect, useState } from "react";
import { getHealth } from "./api";

export default function App() {
  const [apiState, setApiState] = useState({
    loading: true,
    online: false,
    message: "Checking backend...",
  });

  useEffect(() => {
    getHealth()
      .then((data) => {
        setApiState({
          loading: false,
          online: data.status === "ok",
          message: `${data.service} is online`,
        });
      })
      .catch(() => {
        setApiState({
          loading: false,
          online: false,
          message: "Backend is not reachable",
        });
      });
  }, []);

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">PORTFOLIO PROJECT</p>
        <h1>Helpdesk Ticketing System</h1>
        <p className="subtitle">
          Django REST Framework + React
        </p>

        <div className={`status ${apiState.online ? "online" : "offline"}`}>
          <span className="status-dot" />
          <span>{apiState.loading ? "Checking backend..." : apiState.message}</span>
        </div>

        <div className="cards">
          <article>
            <h2>Customer</h2>
            <p>Create tickets, follow status, and reply to support.</p>
          </article>

          <article>
            <h2>Support Agent</h2>
            <p>Assign, prioritize, respond to, and resolve tickets.</p>
          </article>
        </div>
      </section>
    </main>
  );
}
