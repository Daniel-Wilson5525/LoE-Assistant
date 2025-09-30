import React from "react";
export default function Stepper({ step }) {
  const steps = ["Paste", "Edit", "Generate"];
  return (
    <div className="flex items-center gap-4 text-sm text-slate-600 mb-6">
      {steps.map((label, i) => {
        const idx = i + 1;
        const active = step === idx;
        const done = step > idx;
        return (
          <div key={label} className="flex items-center gap-2">
            <div
              className={`w-7 h-7 flex items-center justify-center rounded-full border 
                ${active ? "bg-blue-600 text-white border-blue-600"
                         : done ? "bg-green-600 text-white border-green-600"
                                : "border-slate-300 text-slate-500"}`}
            >
              {idx}
            </div>
            <span className={`${active ? "font-semibold text-slate-900" : ""}`}>{label}</span>
            {i < steps.length - 1 && <div className="w-10 h-px bg-slate-200 mx-2" />}
          </div>
        );
      })}
    </div>
  );
}
