import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { SimulateMessage } from "../components/simulate-message";

const postMock = jest.fn();
jest.mock("@selph/shared", () => ({ apiClient: { post: (...a: unknown[]) => postMock(...a) } }));

describe("SimulateMessage", () => {
  beforeEach(() => postMock.mockReset());

  it("disables submit until a message is typed", () => {
    render(<SimulateMessage onIngested={jest.fn()} />);
    expect(screen.getByRole("button", { name: /send to my twin/i })).toBeDisabled();
  });

  it("posts to /messages/ingest, reports the draft and refreshes", async () => {
    postMock.mockResolvedValue({ data: { draft_id: "d1", status: "draft_ready" } });
    const onIngested = jest.fn();
    render(<SimulateMessage onIngested={onIngested} />);

    fireEvent.change(screen.getByLabelText("Sender name"), { target: { value: "Priya Rao" } });
    fireEvent.change(screen.getByLabelText("Message"), { target: { value: "How do you stay focused?" } });
    fireEvent.click(screen.getByRole("button", { name: /send to my twin/i }));

    await waitFor(() => expect(onIngested).toHaveBeenCalled());
    expect(postMock).toHaveBeenCalledWith("/messages/ingest", {
      channel: "instagram_dm",
      sender_name: "Priya Rao",
      sender_id: "priya_rao",
      content: "How do you stay focused?",
    });
    expect(screen.getByText(/draft created/i)).toBeInTheDocument();
  });

  it("explains VIP routing and shows API errors", async () => {
    postMock.mockResolvedValueOnce({ data: { draft_id: null, routing_action: "direct_notify" } });
    render(<SimulateMessage onIngested={jest.fn()} />);
    fireEvent.change(screen.getByLabelText("Message"), { target: { value: "term sheet" } });
    fireEvent.click(screen.getByRole("button", { name: /send to my twin/i }));
    expect(await screen.findByText(/VIP sender/i)).toBeInTheDocument();

    postMock.mockRejectedValueOnce({ response: { data: { detail: "boom" } } });
    fireEvent.change(screen.getByLabelText("Message"), { target: { value: "again" } });
    fireEvent.click(screen.getByRole("button", { name: /send to my twin/i }));
    expect(await screen.findByText("boom")).toBeInTheDocument();
  });
});
