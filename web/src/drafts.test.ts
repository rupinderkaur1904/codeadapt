import { clearAllDrafts, clearDraftsExcept, loadDraft, saveDraft } from "./drafts";

describe("drafts", () => {
  beforeEach(() => window.localStorage.clear());

  it("keeps each account's drafts separate", () => {
    saveDraft("alice", "count-occurrences", "// alice");
    expect(loadDraft("alice", "count-occurrences")).toBe("// alice");
    expect(loadDraft("bob", "count-occurrences")).toBeNull();
  });

  it("does not confuse usernames that share a prefix", () => {
    saveDraft("al", "x:y", "// al");
    expect(loadDraft("al:x", "y")).toBeNull();
    clearDraftsExcept("al:x");
    expect(loadDraft("al", "x:y")).toBeNull();
  });

  it("clears every draft on logout and leaves other keys alone", () => {
    saveDraft("alice", "lower-bound", "// a");
    saveDraft("bob", "lower-bound", "// b");
    window.localStorage.setItem("codeadapt:draft:lower-bound", "// legacy");
    window.localStorage.setItem("codeadapt:dev-role", "student");
    clearAllDrafts();
    expect(window.localStorage.length).toBe(1);
    expect(window.localStorage.getItem("codeadapt:dev-role")).toBe("student");
  });

  it("keeps only the logged-in account's drafts on login", () => {
    saveDraft("alice", "lower-bound", "// a");
    saveDraft("bob", "lower-bound", "// b");
    window.localStorage.setItem("codeadapt:draft:lower-bound", "// legacy");
    clearDraftsExcept("bob");
    expect(loadDraft("bob", "lower-bound")).toBe("// b");
    expect(loadDraft("alice", "lower-bound")).toBeNull();
    expect(window.localStorage.getItem("codeadapt:draft:lower-bound")).toBeNull();
  });
});
