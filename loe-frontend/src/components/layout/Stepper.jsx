import React from "react";

export default function Stepper({ step = 1 }) {
  const steps = [
    { n: 1, label: "Upload / Paste" },
    { n: 2, label: "Review Fields" },
    { n: 3, label: "Generate" },
  ];

  return (
    <div className="mb-6">
      <div className="flex items-center gap-3 text-sm">
        {steps.map((s, idx) => {
          const active = s.n === step;
          const done = s.n < step;
          return (
            <React.Fragment key={s.n}>
              <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border
                               ${active ? "bg-slate-900 text-white border-slate-900"
                                        : done ? "bg-green-50 text-green-700 border-green-200"
                                               : "bg-white text-slate-600 border-slate-200"}`}>
                <span className={`h-5 w-5 grid place-items-center rounded-full text-xs
                                 ${active ? "bg-white text-slate-900"
                                          : done ? "bg-green-600 text-white"
                                                 : "bg-slate-100 text-slate-600"}`}>
                  {s.n}
                </span>
                <span className="font-medium">{s.label}</span>
              </div>
              {idx < steps.length - 1 && (
                <div className="h-px flex-1 bg-slate-200" />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
