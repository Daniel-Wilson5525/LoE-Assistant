import { Routes, Route, Navigate } from "react-router-dom";
import Header from "./components/layout/Header.jsx";

function Home() {
  return (
    <div className="page">
      <h1>LOE Assistant</h1>
      <p>Select an assistant from the top menu to begin.</p>
    </div>
  );
}

function RackStack() {
  return (
    <div className="page">
      <h1>Rack &amp; Stack</h1>
      <p>🧰 This is the placeholder page for the Rack &amp; Stack assistant.</p>
      <p>You can drop your 3-step flow here later.</p>
    </div>
  );
}

export default function App() {
  return (
    <>
      <Header />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/assistants/rack-stack" element={<RackStack />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
