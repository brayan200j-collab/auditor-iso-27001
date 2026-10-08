import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { surveyCopy } from "@/content/es";

import { surveySchema } from "./schemas";
import { SurveyForm } from "./SurveyForm";

const submitSurveyAction = vi.fn();
const push = vi.fn();

vi.mock("./actions", () => ({
  submitSurveyAction: (id: string, input: unknown) => submitSurveyAction(id, input),
}));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

describe("surveySchema", () => {
  it("accepts comma decimals and rejects out-of-range hours", () => {
    const base = {
      usefulness: "5",
      ease_of_use: "4",
      trust_in_results: "3",
      actionable_recommendations: "yes",
      manual_time_hours: "1,5",
      system_time_hours: "0.5",
      willingness_to_use: "4",
      willingness_to_pay: "MAYBE",
      comments: "",
    };
    const parsed = surveySchema.parse(base);
    expect(parsed.manual_time_hours).toBe(1.5);
    expect(surveySchema.safeParse({ ...base, system_time_hours: "1001" }).success).toBe(false);
    expect(surveySchema.safeParse({ ...base, manual_time_hours: "abc" }).success).toBe(false);
    expect(surveySchema.safeParse({ ...base, manual_time_hours: " " }).success).toBe(false);
  });
});

describe("SurveyForm", () => {
  beforeEach(() => {
    submitSurveyAction.mockReset();
    push.mockReset();
  });

  it("asks for every answer in Spanish before calling the server", async () => {
    render(<SurveyForm evaluationId="eval-1" />);
    await userEvent.click(screen.getByRole("button", { name: surveyCopy.submit }));
    expect(await screen.findAllByText(surveyCopy.required)).toHaveLength(6);
    expect(screen.getAllByText(surveyCopy.hoursInvalid)).toHaveLength(2);
    expect(submitSurveyAction).not.toHaveBeenCalled();
  });

  it("submits the answers and returns to the results", async () => {
    submitSurveyAction.mockResolvedValue({ ok: true, message: surveyCopy.sent });
    render(<SurveyForm evaluationId="eval-1" />);
    const user = userEvent.setup();
    for (const question of [
      surveyCopy.questions.usefulness,
      surveyCopy.questions.ease_of_use,
      surveyCopy.questions.trust_in_results,
      surveyCopy.questions.willingness_to_use,
    ]) {
      const group = screen.getByRole("group", { name: question });
      await user.click(group.querySelector('input[value="4"]') as HTMLInputElement);
    }
    const pick = async (question: string, value: string) =>
      user.click(
        screen
          .getByRole("group", { name: question })
          .querySelector(`input[value="${value}"]`) as HTMLInputElement,
      );
    await pick(surveyCopy.questions.actionable_recommendations, "yes");
    await pick(surveyCopy.questions.willingness_to_pay, "MAYBE");
    await user.type(screen.getByLabelText(surveyCopy.questions.manual_time_hours), "8");
    await user.type(screen.getByLabelText(surveyCopy.questions.system_time_hours), "1,5");
    await user.click(screen.getByRole("button", { name: surveyCopy.submit }));

    await waitFor(() => expect(submitSurveyAction).toHaveBeenCalledTimes(1));
    expect(submitSurveyAction.mock.calls[0]?.[1]).toMatchObject({
      usefulness: "4",
      actionable_recommendations: "yes",
      willingness_to_pay: "MAYBE",
      system_time_hours: "1,5",
    });
    await waitFor(() => expect(push).toHaveBeenCalledWith("/app/evaluaciones/eval-1/resultados"));
  });
});
