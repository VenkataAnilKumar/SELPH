import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BriefingsPanel } from "../components/briefings-panel";
import { VipTiersPanel } from "../components/vip-tiers-panel";

const getMock = jest.fn();
const postMock = jest.fn();
const putMock = jest.fn();
const deleteMock = jest.fn();
jest.mock("@selph/shared", () => ({
  apiClient: {
    get: (...a: unknown[]) => getMock(...a),
    post: (...a: unknown[]) => postMock(...a),
    put: (...a: unknown[]) => putMock(...a),
    delete: (...a: unknown[]) => deleteMock(...a),
  },
}));

const briefing = (over = {}) => ({
  id: "b1", briefing_type: "availability", topic: "conference week",
  content: "At a conference, replies slower", priority: 8, is_active: true,
  use_count: 2, max_uses: null, expires_at: null, cleared_at: null, ...over,
});

beforeEach(() => {
  [getMock, postMock, putMock, deleteMock].forEach((m) => m.mockReset());
});

describe("BriefingsPanel", () => {
  it("lists only active, uncleared briefings", async () => {
    getMock.mockResolvedValue({
      data: { active_count: 1, items: [briefing(), briefing({ id: "b2", topic: "old", cleared_at: "2026-01-01" })] },
    });
    render(<BriefingsPanel />);
    expect(await screen.findByText("conference week")).toBeInTheDocument();
    expect(screen.queryByText("old")).not.toBeInTheDocument();
    expect(screen.getByText(/Used 2 times/)).toBeInTheDocument();
  });

  it("shows an empty state", async () => {
    getMock.mockResolvedValue({ data: { active_count: 0, items: [] } });
    render(<BriefingsPanel />);
    expect(await screen.findByText(/No active briefings/)).toBeInTheDocument();
  });

  it("keeps option labels short and explains the selected type underneath", async () => {
    getMock.mockResolvedValue({ data: { active_count: 0, items: [] } });
    render(<BriefingsPanel />);
    await screen.findByText(/No active briefings/);

    // Long "Label — hint" options were clipped by the select; labels are short and the hint is separate.
    const options = Array.from(screen.getByLabelText("Briefing type").querySelectorAll("option")).map((o) => o.textContent);
    expect(options).toEqual(["Availability", "Instruction", "Fact", "Opinion", "Boundary"]);
    expect(screen.getByTestId("briefing-type-hint")).toHaveTextContent(/added to drafts as a heads-up/i);

    fireEvent.change(screen.getByLabelText("Briefing type"), { target: { value: "boundary" } });
    expect(screen.getByTestId("briefing-type-hint")).toHaveTextContent(/stay away from/i);
  });

  it("requires topic and content, then posts the briefing with an expiry", async () => {
    getMock.mockResolvedValue({ data: { active_count: 0, items: [] } });
    postMock.mockResolvedValue({ data: {} });
    render(<BriefingsPanel />);
    const submit = await screen.findByRole("button", { name: /add briefing/i });
    expect(submit).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Briefing topic"), { target: { value: "launch" } });
    fireEvent.change(screen.getByLabelText("Briefing content"), { target: { value: "Mention my course" } });
    fireEvent.change(screen.getByLabelText("Briefing type"), { target: { value: "instruction" } });
    fireEvent.change(screen.getByLabelText("Briefing priority"), { target: { value: "99" } });
    fireEvent.change(screen.getByLabelText("Expires in hours"), { target: { value: "24" } });
    fireEvent.click(submit);

    await waitFor(() => expect(postMock).toHaveBeenCalled());
    const [url, body] = postMock.mock.calls[0];
    expect(url).toBe("/identity/briefings");
    expect(body).toMatchObject({ briefing_type: "instruction", topic: "launch", content: "Mention my course", priority: 10 });
    const expires = new Date(body.expires_at).getTime() - Date.now();
    expect(expires).toBeGreaterThan(23 * 3600_000);
    expect(expires).toBeLessThan(25 * 3600_000);
    await waitFor(() => expect(getMock.mock.calls.length).toBeGreaterThan(1)); // reloaded
  });

  it("clears a briefing and shows API errors", async () => {
    getMock.mockResolvedValue({ data: { active_count: 1, items: [briefing()] } });
    postMock.mockResolvedValueOnce({ data: {} });
    render(<BriefingsPanel />);
    fireEvent.click(await screen.findByRole("button", { name: /clear briefing conference week/i }));
    await waitFor(() => expect(postMock).toHaveBeenCalledWith("/identity/briefings/b1/clear"));

    postMock.mockRejectedValueOnce({ response: { data: { detail: "nope" } } });
    fireEvent.click(await screen.findByRole("button", { name: /clear briefing conference week/i }));
    expect(await screen.findByText("nope")).toBeInTheDocument();
  });
});

describe("VipTiersPanel", () => {
  const tier = (over = {}) => ({
    id: "t1", sender_id: "james@cofounder.com", platform: "gmail", tier: 0, tier_label: "Co-founder", ...over,
  });

  it("lists senders with a readable tier", async () => {
    getMock.mockResolvedValue({ data: { total: 1, items: [tier()] } });
    render(<VipTiersPanel />);
    expect(await screen.findByText("Co-founder")).toBeInTheDocument();
    expect(screen.getByText("VIP — bypass twin", { selector: "span" })).toBeInTheDocument();
    expect(screen.getByText(/james@cofounder.com · gmail/)).toBeInTheDocument();
  });

  it("saves a sender tier via PUT", async () => {
    getMock.mockResolvedValue({ data: { total: 0, items: [] } });
    putMock.mockResolvedValue({ data: {} });
    render(<VipTiersPanel />);
    const save = await screen.findByRole("button", { name: /save sender/i });
    expect(save).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Sender ID"), { target: { value: "  partner@vc.com " } });
    fireEvent.change(screen.getByLabelText("Platform"), { target: { value: "gmail" } });
    fireEvent.change(screen.getByLabelText("Tier"), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText("Label"), { target: { value: "Investor" } });
    fireEvent.click(save);

    await waitFor(() =>
      expect(putMock).toHaveBeenCalledWith("/identity/sender-tiers", {
        sender_id: "partner@vc.com", platform: "gmail", tier: 1, tier_label: "Investor",
      })
    );
  });

  it("removes a sender with an URL-encoded path", async () => {
    getMock.mockResolvedValue({ data: { total: 1, items: [tier()] } });
    deleteMock.mockResolvedValue({});
    render(<VipTiersPanel />);
    fireEvent.click(await screen.findByRole("button", { name: /remove james@cofounder.com/i }));
    await waitFor(() =>
      expect(deleteMock).toHaveBeenCalledWith("/identity/sender-tiers/gmail/james%40cofounder.com")
    );
  });

  it("shows an empty state", async () => {
    getMock.mockResolvedValue({ data: { total: 0, items: [] } });
    render(<VipTiersPanel />);
    expect(await screen.findByText(/No special senders yet/)).toBeInTheDocument();
  });
});
