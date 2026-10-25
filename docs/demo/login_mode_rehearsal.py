"""Login-mode demo rehearsal against docs/demo/login_mode_start.sh (port 8010).

Run from backend/: uv run --with httpx python ../docs/demo/login_mode_rehearsal.py
Synthetic demo accounts only; checks the mechanism, not accuracy.
"""
import json, time, pathlib, httpx
B = "http://127.0.0.1:8010/api/v1"
C = pathlib.Path(__file__).resolve().parents[2] / "content" / "demo" / "lower-bound"

def login(user, pw):
    c = httpx.Client(timeout=30)
    r = c.post(f"{B}/auth/login", json={"username": user, "password": pw})
    r.raise_for_status()
    # Secure cookie: browsers accept it on http://localhost, httpx does not, so send it by hand.
    cookie = "; ".join(f"{k}={v}" for k, v in r.cookies.items())
    c.headers.update({"Cookie": cookie, "X-CSRF-Token": r.json()["csrf_token"]})
    return c

anon = httpx.Client()
print("1. no session, dev header ignored:", anon.get(f"{B}/problems", headers={"X-Dev-Role": "researcher"}).status_code)
print("   wrong password:", anon.post(f"{B}/auth/login", json={"username": "demo-student", "password": "x"}).status_code)
st = login("demo-student", "student demo password")
print("2. student me:", st.get(f"{B}/auth/me").json()["role"], "| problems:", len(st.get(f"{B}/problems").json()))
src = (C / "error_models" / "exact_match_sentinel.cpp").read_text()
sid = st.post(f"{B}/submissions", json={"problem_slug": "lower-bound", "source": src}).json()["id"]
t0 = time.time()
while True:
    v = st.get(f"{B}/submissions/{sid}").json()
    if v["status"] in ("completed", "failed"): break
    time.sleep(1)
body = json.dumps(v)
print(f"3. buggy submission: {v['status']} in {time.time()-t0:.0f}s; internal label hidden from student:", "exact_match_sentinel" not in body, "| P(known) hidden:", "p_known" not in body)
print("   student blocked from research:", st.get(f"{B}/research/submissions").status_code, st.get(f"{B}/research/learner-model", params={"username": "demo-student"}).status_code)
print("   no CSRF token -> ", httpx.post(f"{B}/submissions", json={"problem_slug": "lower-bound", "source": src}, headers={"Cookie": st.headers["Cookie"]}).status_code)
rs = login("demo-researcher", "researcher demo password")
rows = rs.get(f"{B}/research/submissions").json()
print("4. researcher list:", [(r["username"], r["outcome"], r["selected_model"]) for r in rows])
tr = rs.get(f"{B}/research/submissions/{sid}/trace").json()
print("   trace diagnosis:", tr["diagnosis"]["method"], tr["diagnosis"]["outcome"], tr["diagnosis"]["selected_model"])
lm = rs.get(f"{B}/research/learner-model", params={"username": "demo-student"}).json()
print("   learner model:", lm["estimate"]["label"], [(s["skill"], s["state"], [o["observation"]["value"] for o in s["observations"]]) for s in lm["estimate"]["skills"]])
print("5. logout:", rs.post(f"{B}/auth/logout").status_code, "-> me after logout:", rs.get(f"{B}/auth/me").status_code)
