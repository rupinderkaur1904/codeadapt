import { useQuery, useQueryClient } from "@tanstack/react-query";
import { lazy, Suspense, useCallback, useState } from "react";
import { Link, NavLink, Route, Routes, useLocation } from "react-router-dom";

import { ApiError, api, setCsrfToken } from "./api/client";
import { ErrorMessage } from "./components/ErrorMessage";
import { Intro, introSeen } from "./components/Intro";
import { type DevRole, getDevRole, setDevRole } from "./devRole";

import { LandingPage } from "./pages/LandingPage";
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
const LearnersPage = lazy(() =>
  import("./pages/LearnersPage").then((m) => ({ default: m.LearnersPage })),
);
const AttemptsPage = lazy(() =>
  import("./pages/AttemptsPage").then((m) => ({ default: m.AttemptsPage })),
);
const LearnerModelPage = lazy(() =>
  import("./pages/LearnerModelPage").then((m) => ({ default: m.LearnerModelPage })),
);

function Brand() {
  return (
    <Link to="/" className="brand">
      <svg viewBox="0 0 26 26" aria-hidden="true">
        <path d="M13 13 V5" stroke="#7cb868" strokeWidth="2" />
        <path d="M13 9 C11 4 6 3 3 4 C5 8 9 10 13 9Z" fill="#7cb868" />
        <path d="M13 9 C15 4 20 3 23 4 C21 8 17 10 13 9Z" fill="#7cb868" />
        <path
          d="M13 13 L8 22 M13 13 L18 22 M13 13 L13 24"
          stroke="#c9822f"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
      </svg>
      CodeAdapt
    </Link>
  );
}

export function App() {
  const location = useLocation();
  // The intro opens the site only at the landing page, so deep links go straight through.
  const [intro, setIntro] = useState(() => location.pathname === "/" && !introSeen());
  const done = useCallback(() => setIntro(false), []);
  return (
    <>
      {intro && <Intro onDone={done} />}
      <div inert={intro}>
        <AppShell />
      </div>
    </>
  );
}

function AppShell() {
  const location = useLocation();
  const landing = location.pathname === "/";
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
    // The landing page is public; every other page asks for a login.
    if (landing) {
      return (
        <div className="app">
          <header className="app-header">
            <Brand />
            <nav>
              <Link to="/problems">Log in</Link>
            </nav>
          </header>
          <main className="landing-main">
            <LandingPage loggedIn={false} />
          </main>
        </div>
      );
    }
    return (
      <div className="app">
        <header className="app-header">
          <Brand />
        </header>
        <main>
          <LoginPage
            onLoggedIn={(user) => {
              setCsrfToken(user.csrf_token ?? null);
              // Drop every cached response and refetch as the new account.
              void queryClient.resetQueries();
            }}
          />
        </main>
      </div>
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
        <Brand />
        <nav>
          <NavLink to="/problems">Problems</NavLink>
          <NavLink to="/attempts">My attempts</NavLink>
          {role !== "student" && (
            <>
              <NavLink to="/research" end>
                Research
              </NavLink>
              <NavLink to="/research/learners">Learners</NavLink>
            </>
          )}
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
      <main className={landing ? "landing-main" : undefined}>
        <Suspense fallback={<p>Loading…</p>}>
          <Routes>
            <Route path="/" element={<LandingPage loggedIn />} />
            <Route path="/problems" element={<ProblemListPage />} />
            <Route path="/practice/:slug" element={<PracticePage />} />
            <Route path="/attempts" element={<AttemptsPage />} />
            <Route path="/research" element={<ResearchPage />} />
            <Route path="/research/learners" element={<LearnersPage />} />
            <Route path="/research/submissions/:id" element={<TracePage />} />
            <Route path="/research/learners/:username" element={<LearnerModelPage />} />
            <Route path="*" element={<p>Page not found.</p>} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}
