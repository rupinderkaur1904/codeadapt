import { lazy, Suspense } from "react";
import { Link, Route, Routes } from "react-router-dom";

import { ProblemListPage } from "./pages/ProblemListPage";

// The editor bundle is large; load it only when a problem is opened.
const PracticePage = lazy(() =>
  import("./pages/PracticePage").then((m) => ({ default: m.PracticePage })),
);

export function App() {
  return (
    <div className="app">
      <header className="app-header">
        <Link to="/" className="brand">
          CodeAdapt
        </Link>
      </header>
      <main>
        <Suspense fallback={<p>Loading…</p>}>
          <Routes>
            <Route path="/" element={<ProblemListPage />} />
            <Route path="/practice/:slug" element={<PracticePage />} />
            <Route path="*" element={<p>Page not found.</p>} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}
