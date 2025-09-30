import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Header from "./components/layout/Header.jsx";
import Home from "./pages/Home.jsx";
import RackStack from "./pages/assistants/RackStack.jsx";
import "./styles/app.css";

export default function App() {
  return (
    <>
      <Header />
      <main className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/assistants/rack-stack" element={<RackStack />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  );
}
