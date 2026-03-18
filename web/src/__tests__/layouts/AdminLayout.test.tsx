import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ConfigProvider } from "antd";
import { AdminLayout } from "../../layouts/AdminLayout";
import { useAuth } from "../../stores/auth";

beforeEach(() => {
  useAuth.setState({
    token: "test-token",
    isAuthenticated: true,
    isLoading: false,
    error: null,
  });
});

function renderLayout() {
  return render(
    <ConfigProvider>
      <MemoryRouter>
        <AdminLayout />
      </MemoryRouter>
    </ConfigProvider>,
  );
}

describe("AdminLayout", () => {
  it("renders 5 menu items", () => {
    renderLayout();
    expect(screen.getByText("\u041a\u0430\u043b\u0435\u043d\u0434\u0430\u0440\u044c")).toBeInTheDocument();
    expect(screen.getByText("\u041a\u043b\u0438\u0435\u043d\u0442\u044b")).toBeInTheDocument();
    expect(screen.getByText("\u0423\u0441\u043b\u0443\u0433\u0438")).toBeInTheDocument();
    expect(screen.getByText("\u041f\u043b\u0430\u0442\u0435\u0436\u0438")).toBeInTheDocument();
    expect(screen.getByText("\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438")).toBeInTheDocument();
  });

  it("renders theme toggle button", () => {
    renderLayout();
    // The Switch component with BulbOutlined is the theme toggle
    const switchEl = document.querySelector(".ant-switch");
    expect(switchEl).toBeInTheDocument();
  });
});
