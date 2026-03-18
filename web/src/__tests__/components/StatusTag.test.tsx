import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BookingStatusTag, PaymentStatusTag } from "../../components/StatusTag";

describe("BookingStatusTag", () => {
  it("renders with correct label for 'confirmed' status", () => {
    render(BookingStatusTag({ status: "confirmed" }));
    expect(screen.getByText("\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0430")).toBeInTheDocument();
  });
});

describe("PaymentStatusTag", () => {
  it("renders with correct label for 'paid' status", () => {
    render(PaymentStatusTag({ status: "paid" }));
    expect(screen.getByText("\u041e\u043f\u043b\u0430\u0447\u0435\u043d")).toBeInTheDocument();
  });
});
