import React, { useEffect, useMemo, useState } from "react";
import { generateLoE } from "../../lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import AppShell from "../layout/AppShell";
import StepNav from "../layout/StepNav";

/* strip duplicate headings injected by the model/system */
const stripHeading = (text = "", head = "PROJECT SUMMARY") =>
  String(text || "").replace(new RegExp(`^\\s*${head}\\s*\\n`, "i"), "");

function Tabs({ value, onChange }) {
  const items = ["Summary", "Tasks"];
  return (
    <div className="inline-flex rounded-xl border bg-white p-1">
      {items.map((t) => (
        <button
          key={t}
          onClick={() => onChange(t)}
          className={`px-3 py-1.5 text-sm rounded-lg transition
            ${value===t ? "bg-slate-900 text-white" : "hover:bg-slate-50"}`}
        >
          {t}
        </button>
      ))}
    </div>
  );
}

export default function GenerateStep({ schema, onBack }) {
  const [out, setOut] = useState(null);
  const [tab, setTab] = useState("Summary");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setErr(""); setLoading(true);
      try {
        const resp = await generateLoE(schema);
        if (!cancelled) setOut(resp);
      } catch (e) {
        if (!cancelled) setErr(e.message || "Generate failed");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [schema]);

  const summary = useMemo(() => stripHeading(out?.summary, "PROJECT SUMMARY"), [out]);
  const tasks   = useMemo(() => stripHeading(out?.tasks,   "PROJECT TASKS"),   [out]);

  const rightHeader =
    <div className="flex gap-2">
      {onBack && (
        <button onClick={onBack}
          className="px-3 py-2 rounded-lg border border-slate-300 bg-white hover:bg-slate-50">
          Back to Edit
        </button>
      )}
      {out && (
        <>
          <button
            onClick={() => navigator.clipboard.writeText(`${summary}\n\n${tasks}`)}
            className="px-3 py-2 rounded-lg bg-slate-900 text-white"
          >
            Copy
          </button>
          <button
            onClick={() => {
              const blob = new Blob(
                [`# Project Summary\n\n${summary}\n\n# Project Tasks\n\n${tasks}\n\n# Open Questions\n\n- ${(out.open_questions||[]).join("\n- ")}`],
                { type: "text/markdown;charset=utf-8" }
              );
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url; a.download = "LoE.md"; a.click(); URL.revokeObjectURL(url);
            }}
            className="px-3 py-2 rounded-lg border border-slate-300 bg-white hover:bg-slate-50"
          >
            Download .md
          </button>
        </>
      )}
    </div>;

  return (
    <AppShell title="Rack & Stack Assistant" rightSlot={rightHeader}>
      {/* Grid: left content + right sidebar stepper */}
      <div className="grid grid-cols-1 lg:grid-cols-[240px_minmax(0,1fr)] gap-6">
        <StepNav step={2} />

        <div className="space-y-6">
          {/* Alerts / loading */}
          {err && (
            <div className="p-4 rounded-xl border border-red-200 bg-red-50 text-red-800">
              <strong className="block mb-1">Generation error</strong>
              <div className="whitespace-pre-wrap text-sm">{err}</div>
            </div>
          )}

          {loading && !out && !err && (
            <div className="rounded-2xl border bg-white p-6">
              <div className="h-4 w-32 mb-4 bg-slate-200 rounded" />
              <div className="h-3 w-full mb-2 bg-slate-100 rounded" />
              <div className="h-3 w-11/12 mb-2 bg-slate-100 rounded" />
              <div className="h-3 w-10/12 bg-slate-100 rounded" />
              <p className="mt-4 text-sm text-slate-500">Generating…</p>
            </div>
          )}

          {/* Content card with tabs */}
          {out && !err && (
            <>
              <div className="rounded-2xl border bg-white p-6">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-lg font-semibold">Generated LoE</h2>
                  <Tabs value={tab} onChange={setTab} />
                </div>
                <article className="prose max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {(tab === "Summary" ? summary : tasks) || ""}
                  </ReactMarkdown>
                </article>
              </div>

              <div className="rounded-2xl border bg-white p-6">
                <h3 className="font-semibold mb-2">Open Questions</h3>
                <ul className="list-disc pl-5">
                  {(out.open_questions || []).map((q, i) => <li key={i}>{q}</li>)}
                </ul>
              </div>
            </>
          )}
        </div>
      </div>
    </AppShell>
  );
}
