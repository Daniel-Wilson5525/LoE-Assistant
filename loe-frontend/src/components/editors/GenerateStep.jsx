import React from "react";
import { useState } from "react";
import { generateLoE } from "../../lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function GenerateStep({ schema }) {
  const [out, setOut] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const run = async () => {
    setErr(""); setLoading(true);
    try {
      const resp = await generateLoE(schema);
      setOut(resp);
    } catch (e) {
      setErr(e.message || "Generate failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl">
      {!out && (
        <button
          className="px-4 py-2 rounded-lg bg-blue-600 text-white"
          disabled={loading}
          onClick={run}
        >
          {loading ? "Generating…" : "Generate LOE"}
        </button>
      )}

      {err && <p className="text-red-600 mt-3">{err}</p>}

      {out && (
        <div className="mt-4 space-y-8">
          <section>
            <h3 className="text-xl font-bold mb-2">Project Summary</h3>
            <article className="prose max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{out.summary || ""}</ReactMarkdown>
            </article>
          </section>
          <section>
            <h3 className="text-xl font-bold mb-2">Project Tasks</h3>
            <article className="prose max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{out.tasks || ""}</ReactMarkdown>
            </article>
          </section>
          <section>
            <h3 className="text-xl font-bold mb-2">Open Questions</h3>
            <ul className="list-disc pl-5">
              {(out.open_questions || []).map((q, i) => <li key={i}>{q}</li>)}
            </ul>
          </section>
        </div>
      )}
    </div>
  );
}
