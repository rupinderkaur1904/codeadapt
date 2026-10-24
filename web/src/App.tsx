import { useQuery, useQueryClient } from "@tanstack/react-query";
import { lazy, Suspense, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";

import { ApiError, api, setCsrfToken } from "./api/client";
import { ErrorMessage } from "./components/ErrorMessage";
import { type DevRole, getDevRole, setDevRole } from "./devRole";

import { LoginPage } from "./pages/LoginPage";
import { ProblemListPage } from "./pages/ProblemListPage";

// The editor bundle is large; load it only when a problem is opened.
const PracticePage = lazy(() =>
  import("./pages/PracticePage").then((m) => ({ default: m.PracticePage })),
);

const ResearchPage = lazy(() =>
  import("./pages/ResearchPage").then((m) => ({ default: m.ResearchPage })),
);
const TracePage = lazy(() => import("./pages/TracePage").then((m) => ({ default: m.TracePage })));
const LearnerModelPage = lazy(() =>
  import("./pages/LearnerModelPage").then((m) => ({ default: m.LearnerModelPage })),
);

export function App() {
  const queryClient = useQueryClient();
  const [devRole, setRole] = useState<DevRole>(getDevRole);
  const me = useQuery({
    queryKey: ["me", devRole],
    queryFn: async () => {
      const user = await api.me();
      setCsrfToken(user.csrf_token ?? null);
      return user;
    },
    retry: false,
  });

  if (me.isPending) return <p>Loading…</p>;
  if (me.error instanceof ApiError && me.error.status === 401) {
    return (
      <LoginPage
        onLoggedIn={(user) => {
          setCsrfToken(user.csrf_token ?? null);
          // Drop every cached response and refetch as the new account.
          void queryClient.resetQueries();
        }}
      />
    );
  }
  if (me.error) return <ErrorMessage error={me.error} />;

  const user = me.data;
  // A real session carries a CSRF token; the development stub has none.
  const devStub = user.csrf_token == null;
  const role = user.role;
  return (
    <div className="app">
      <header className="app-header">
        <Link to="/" className="brand">
          CodeAdapt
        </Link>
        <nav>
          <Link to="/">Problems</Link>
          {role !== "student" && <Link to="/research">Research</Link>}
        </nav>
        {!devStub && (
          <span className="account">
            {user.username}
            <button
              type="button"
              onClick={() => {
                void api.logout().finally(() => {
                  setCsrfToken(null);
                  void queryClient.resetQueries();
                });
              }}
            >
              Log out
            </button>
          </span>
        )}
        {devStub && (
          <label className="dev-role">
            Development role{" "}
            <select
              value={devRole}
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
        )}
      </header>
      <main>
        <Suspense fallback={<p>Loading…</p>}>
          <Routes>
            <Route path="/" element={<ProblemListPage />} />
            <Route path="/practice/:slug" element={<PracticePage />} />
            <Route path="/research" element={<ResearchPage />} />
            <Route path="/research/submissions/:id" element={<TracePage />} />
            <Route path="/research/learners/:username" element={<LearnerModelPage />} />
            <Route path="*" element={<p>Page not found.</p>} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}
