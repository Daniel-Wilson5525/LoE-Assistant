import React, { useEffect, useMemo, useRef, useState } from "react";
import { generateLoE } from "../../lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import AppShell from "../layout/AppShell";

/* strip duplicate headings injected by the model/system */
const stripHeading = (text = "", head = "PROJECT SUMMARY") =>
  String(text || "").replace(new RegExp(`^\\s*${head}\\s*\\n`, "i"), "");

/** Build the full markdown for copy/download */
function buildMarkdown(summary, tasks = "") {
  return `# Project Summary\n\n${summary || ""}\n\n# Project Tasks\n\n${tasks || ""}\n`;
}


export default function GenerateStep({ schema, onBack }) {
  const [out, setOut] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const runId = useRef(0);

    useEffect(() => {
      let cancelled = false;
      let done = false;

      (async () => {
        setErr(""); setLoading(true);
        try {
          if (done) return;
          done = true; // guard inside the effect
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

  const copyAll = () => {
    const text = buildMarkdown(summary, tasks);
    navigator.clipboard.writeText(text);
  };

  const downloadMd = () => {
    const blob = new Blob([buildMarkdown(summary, tasks)], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "LoE.md"; a.click();
    URL.revokeObjectURL(url);
  };

  const rightHeader = null; 

  return (
    <AppShell title="Rack & Stack Assistant" rightSlot={rightHeader}>
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

        {/* Stacked report: Summary → Tasks */}
        {out && !err && (
          <>
            {/* Summary */}
            <div className="panel">
              <div className="panel-header">
                <div className="section-title">
                  <span className="icon">📄</span>
                  <h2 className="h2">Project Summary</h2>
                  <span className="badge info">read-only</span>
                </div>
              </div>
              <div className="panel-body">
                <article className="prose max-w-none markdown-body">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {summary || ""}
                  </ReactMarkdown>
                </article>
              </div>
            </div>

            {/* Tasks */}
            <div className="panel">
              <div className="panel-header">
                <div className="section-title">
                  <span className="icon">✅</span>
                  <h2 className="h2">Project Tasks</h2>
                  <span className="badge">checklist</span>
                </div>
              </div>
              <div className="panel-body">
                <article className="prose max-w-none markdown-body">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {tasks || ""}
                  </ReactMarkdown>
                </article>
              </div>
            </div>

            {/* Footer export bar */}
            <div className="export-bar">
              <div className="export-bar-inner">
                <span className="muted small">Export</span>
                <div className="export-actions">
                  <button onClick={copyAll} className="btn">Copy All</button>
                  <button onClick={downloadMd} className="btn-secondary">Download .md</button>
                </div>
              </div>
            </div>
          </>
        )}

      </div>
    </AppShell>
  );
}
