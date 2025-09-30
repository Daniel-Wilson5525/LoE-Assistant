import React, { useState } from "react";
import Stepper from "../../components/layout/Stepper";
import PasteStep from "../../components/editors/PasteStep";
import EditStep from "../../components/editors/EditStep";
import GenerateStep from "../../components/editors/GenerateStep";


export default function RackStack() {
  const [step, setStep] = useState(1);
  const [schema, setSchema] = useState(null);

  return (
    <div className="max-w-6xl mx-auto py-8">
      <h1 className="text-2xl font-bold mb-1">Rack &amp; Stack Assistant</h1>
      <p className="text-slate-600 mb-6">
        Paste request → review extracted fields → generate the LOE.
      </p>

      <Stepper step={step} />

      {step === 1 && (
        <PasteStep
          onIngested={(sc) => {
            setSchema(sc);
            setStep(2);
          }}
          defaultLoeType="rack_stack"
        />
      )}

      {step === 2 && schema && (
        <EditStep
          schema={schema}
          onSchemaChange={setSchema}
          onNext={() => setStep(3)}
        />
      )}

      {step === 3 && schema && <GenerateStep schema={schema} />}
    </div>
  );
}
