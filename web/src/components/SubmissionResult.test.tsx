import { render, screen } from "@testing-library/react";

import { compileError, supported } from "../test/fixtures";
import { SubmissionResult } from "./SubmissionResult";

describe("SubmissionResult", () => {
  it("shows feedback, hint, related cases and per-test verdicts", () => {
    render(<SubmissionResult submission={supported} />);
    expect(screen.getByTestId("feedback")).toHaveTextContent("pattern");
    expect(screen.getByText(/Can your search ever return/)).toBeInTheDocument();
    expect(screen.getByText("Tests: 1 of 2 passed")).toBeInTheDocument();
    expect(screen.getByText("Wrong output")).toBeInTheDocument();
    // Sample tests show their data.
    expect(screen.getByText("L 4 1 3 5 7 5")).toBeInTheDocument();
  });

  it("renders hidden tests without inputs or outputs", () => {
    render(<SubmissionResult submission={supported} />);
    const hiddenRow = screen.getAllByRole("row")[2];
    expect(hiddenRow).toHaveTextContent("The target is larger than every element.");
    expect(hiddenRow?.querySelector("dl")).toBeNull();
  });

  it("shows compiler output and no test table on compile errors", () => {
    render(<SubmissionResult submission={compileError} />);
    expect(screen.getByText(/expected ';'/)).toBeInTheDocument();
    expect(screen.queryByRole("table")).toBeNull();
  });

  it.each([
    ["queued", "Waiting to run"],
    ["running", "Running your code"],
    ["failed", "problem on our side"],
  ] as const)("shows the %s state", (status, text) => {
    render(<SubmissionResult submission={{ ...supported, status }} />);
    expect(screen.getByText(new RegExp(text))).toBeInTheDocument();
    expect(screen.queryByTestId("feedback")).toBeNull();
  });
});
