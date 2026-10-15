import { useQueryClient } from "@tanstack/react-query";
import { lazy, Suspense, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";

import { type DevRole, getDevRole, setDevRole } from "./devRole";

import { ProblemListPage } from "./pages/ProblemListPage";

// The editor bundle is large; load it only when a problem is opened.
const PracticePage = lazy(() =>
  import("./pages/PracticePage").then((m) => ({ default: m.PracticePage })),
);

const ResearchPage = lazy(() =>
  import("./pages/ResearchPage").then((m) => ({ default: m.ResearchPage })),
);
const TracePage = lazy(() => import("./pages/TracePage").then((m) => ({ default: m.TracePage })));

export function App() {
  const queryClient = useQueryClient();
  const [role, setRole] = useState<DevRole>(getDevRole);
  return (
    <div className="app">
      <header className="app-header">
        <Link to="/" className="brand">
          CodeAdapt
        </Link>
        <nav>
          <Link to="/">Problems</Link>
          {role === "researcher" && <Link to="/research">Research</Link>}
        </nav>
        <label className="dev-role">
          Development role{" "}
          <select
            value={role}
            onChange={(e) => {
              const next = e.target.value as DevRole;
              setDevRole(next);
              setRole(next);
              // Every cached response belongs to the previous account.
              queryClient.clear();
            }}
          >
            <option value="student">student</option>
            <option value="researcher">researcher</option>
          </select>
        </label>
      </header>
      <main>
        <Suspense fallback={<p>Loading…</p>}>
          <Routes>
            <Route path="/" element={<ProblemListPage />} />
            <Route path="/practice/:slug" element={<PracticePage />} />
            <Route path="/research" element={<ResearchPage />} />
            <Route path="/research/submissions/:id" element={<TracePage />} />
            <Route path="*" element={<p>Page not found.</p>} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}
