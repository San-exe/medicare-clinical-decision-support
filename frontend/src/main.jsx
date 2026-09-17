import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./index.css";

import App from "./App.jsx";

// Theme
import { ThemeProvider } from "./pages/public/ThemeContext.jsx";


const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error(
    "The client root element was not found."
  );
}

createRoot(rootElement).render(
  <StrictMode>
    <ThemeProvider>
      <App />
    </ThemeProvider>
  </StrictMode>
);