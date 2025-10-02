import React from "react";
import { Link } from "react-router-dom";

export default function Home() {
  return (
    <section className="stack gap-3">
      <h1 className="h1">Welcome</h1>
      <p className="muted">
        Pick an LOE assistant from the navigation. Start with Rack &amp; Stack.
      </p>
      <div>
        <Link className="btn" to="/assistants/rack-stack/1">
          Open Rack &amp; Stack
        </Link>
      </div>
    </section>
  );
}
