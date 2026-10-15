import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { compileError, supported } from "../test/fixtures";
import { AttemptHistory, summarise } from "./AttemptHistory";

describe("AttemptHistory", () => {
  it("summarises attempts", () => {
    expect(summarise(supported)).toBe("1/2 tests passed");
    expect(summarise(compileError)).toBe("Did not compile");
    expect(summarise({ ...supported, status: "queued" })).toBe("Pending");
    expect(summarise({ ...supported, status: "failed" })).toBe("System error");
  });

  it("selects an attempt", async () => {
    const onSelect = vi.fn();
    render(
      <AttemptHistory attempts={[supported, compileError]} selectedId={null} onSelect={onSelect} />,
    );
    await userEvent.click(screen.getByText(/Did not compile/));
    expect(onSelect).toHaveBeenCalledWith("s2");
  });

  it("handles no attempts", () => {
    render(<AttemptHistory attempts={[]} selectedId={null} onSelect={() => {}} />);
    expect(screen.getByText("No attempts yet.")).toBeInTheDocument();
  });
});
