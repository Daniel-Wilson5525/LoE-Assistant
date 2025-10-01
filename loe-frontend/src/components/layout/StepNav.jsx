import React from "react";

const steps = ["Paste", "Edit", "Generate"];

export default function StepNav({ step = 0 }) {
  const pct = ((step + 1) / steps.length) * 100;
  return (
    <aside className="lg:sticky lg:top-20 mb-4 lg:mb-0">
      <div className="rounded-2xl border bg-white/70 backdrop-blur p-4">
        <div className="mb-3">
          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-blue-600 rounded-full transition-all" style={{ width: `${pct}%` }} />
          </div>
        </div>
        <ol className="space-y-2">
          {steps.map((label, i) => (
            <li key={label} className="flex items-center gap-2">
              <span className={`h-6 w-6 shrink-0 rounded-full grid place-items-center text-xs font-semibold
                ${i<=step ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-500"}`}>{i+1}</span>
              <span className={`text-sm ${i===step ? "font-medium text-slate-900" : "text-slate-500"}`}>
                {label}
              </span>
            </li>
          ))}
        </ol>
      </div>
    </aside>
  );
}
