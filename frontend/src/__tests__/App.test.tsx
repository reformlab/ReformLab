// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen } from "@testing-library/react";

import App from "@/App";
import { AppProvider } from "@/contexts/AppContext";

function renderApp() {
  return render(
    <AppProvider>
      <App />
    </AppProvider>,
  );
}

describe("App", () => {
  beforeEach(() => {
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 1600,
    });
    sessionStorage.clear();
  });

  it("shows password prompt when not authenticated", () => {
    renderApp();
    expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /enter/i })).toBeInTheDocument();
  });

  it("renders ReformLab heading on the login page", () => {
    renderApp();
    expect(screen.getByRole("heading", { name: /reformlab/i })).toBeInTheDocument();
  });
});
