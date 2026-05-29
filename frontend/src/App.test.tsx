import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App", () => {
  it("renders the initial PR review workbench shell", () => {
    render(<App />);

    expect(screen.getByText("AI PR Review Assistant")).toBeInTheDocument();
    expect(screen.getByText("Recent Analyses")).toBeInTheDocument();
    expect(screen.getByText("Analyze Pull Request")).toBeInTheDocument();
  });
});
