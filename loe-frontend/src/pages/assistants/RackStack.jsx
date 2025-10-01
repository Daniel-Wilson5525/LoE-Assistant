import React, { useState } from "react";
import PasteStep from "../../components/editors/PasteStep";
import EditStep from "../../components/editors/EditStep";
import GenerateStep from "../../components/editors/GenerateStep";
import AppShell from "../../components/layout/AppShell";   // <— add
import StepNav from "../../components/layout/StepNav";     // <— add
import Stepper from "../../components/layout/Stepper";     // <— add

// keep your current imports…
export default function RackStack() {
  const [step, setStep] = useState(1);
  const [schema, setSchema] = useState(null);

  return (
    <div className="max-w-6xl mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold tracking-tight mb-1">Rack &amp; Stack Assistant</h1>
      <p className="text-slate-600 mb-4">Draft PROJECT SUMMARY and PROJECT TASKS from client requests.</p>

      <div className="rounded-2xl border border-slate-200 bg-white/80 backdrop-blur p-4 mb-6">
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-600">Step {step} of 3</span>
        </div>
        <div className="mt-3">
          <Stepper step={step} />
        </div>
      </div>

      {step === 1 && (
        <PasteStep
          onIngested={(sc) => { setSchema(sc); setStep(2); }}
          defaultLoeType="rack_stack"
        />
      )}

      {step === 2 && schema && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <EditStep
            schema={schema}
            onSchemaChange={setSchema}
            onNext={() => setStep(3)}
          />
        </div>
      )}

      {step === 3 && schema && (
        <GenerateStep
          schema={schema}
          onBack={() => setStep(2)}
        />
      )}
    </div>
  );
}
