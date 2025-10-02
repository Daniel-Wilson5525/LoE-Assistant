import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Header from "./components/layout/Header.jsx";
import Home from "./pages/Home.jsx";
import RackStack from "./pages/assistants/RackStack.jsx";
import "./design/tokens.css";
import "./design/typography.css";
import "./styles/App.css";

export default function App() {
  return (
    <>
      <Header />
      <main className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          {/* Redirect bare path -> step 1 for deep-linkability */}
          <Route
            path="/assistants/rack-stack"
            element={<Navigate to="/assistants/rack-stack/1" replace />}
          />
          <Route path="/assistants/rack-stack/:step" element={<RackStack />} />
          {/* Catch-all redirect to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  );
}
