import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import PasteStep from "../../components/steps/PasteStep";
import EditStep from "../../components/steps/EditStep";
import GenerateStep from "../../components/steps/GenerateStep";
import AppShell from "../../components/layout/AppShell";   
import Stepper from "../../components/layout/Stepper";     
import { useSessionState, clearSessionKeys } from "../../lib/session";


export default function RackStack() {
  const { step: stepParam } = useParams();
  const navigate = useNavigate();
  const step = Math.max(1, Math.min(3, parseInt(stepParam) || 1));
  const [schema, setSchema] = useSessionState("rack_stack_schema", null);

  const goTo = (n) => navigate(`/assistants/rack-stack/${n}`);

  //Reset helper
  const startOver = () => {
    clearSessionKeys(["rack_stack_schema"]);
    setSchema(null);
    goTo(1);
  };

  const steps = [
     { key: "1", label: "Paste" },
     { key: "2", label: "Edit" },
     { key: "3", label: "Generate" },
   ];

  function GuardNoSchema({ targetStep }) {
    return (
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
         <strong className="block mb-1">Nothing to edit yet</strong>
         <p className="text-sm text-slate-700">
           You’re on step {targetStep}, but there isn’t any input yet. Start by pasting or creating a schema.
         </p>
         <button className="mt-3 px-3 py-2 rounded-lg border bg-white hover:bg-slate-50"
                 onClick={() => goTo(1)}>
           Go to Step 1
         </button>
         <button className="px-3 py-2 rounded-lg border bg-white hover:bg-slate-50"
                  onClick={startOver}>
            Start Over
          </button>
       </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 assistant-header">
      <h1 className="text-3xl font-bold tracking-tight mb-1">
        Rack &amp; Stack Assistant
      </h1>

      <p className="assistant-subtitle mb-4">
        Draft PROJECT SUMMARY and PROJECT TASKS from client requests.
      </p>

      <div className="rounded-2xl border border-slate-200 bg-white/80 backdrop-blur p-4 mb-6">
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-600">Step {step} of 3</span>
          <div className="flex gap-2">
            <button className="btn-secondary" onClick={startOver}>Start Over</button>
          </div>
        </div>
        <div className="mt-3">
          <Stepper
           steps={steps}
           currentKey={String(step)}
           onStepChange={(key) => goTo(Number(key))}
          />
        </div>
      </div>

      {step === 1 && (
        <PasteStep
          onIngested={(sc) => { setSchema(sc); goTo(2); }}
          defaultLoeType="rack_stack"
        />
      )}

      {step === 2 && schema && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <EditStep
            schema={schema}
            onSchemaChange={setSchema}
            onNext={() => goTo(3)}
          />
        </div>
      )}
      {step === 2 && !schema && <GuardNoSchema targetStep={2} />}


      {step === 3 && schema && (
        <GenerateStep
          schema={schema}
          onBack={() => goTo(2)}
        />
      )}
      {step === 3 && !schema && <GuardNoSchema targetStep={3} />}
    </div>
  );
}
