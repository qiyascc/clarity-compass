from clarity_ai.context import PageContext
from clarity_ai.prompts import DESIGN_REVIEW_SYSTEM, UNDERSTANDING_SYSTEM
from clarity_ai.provider import Generated, Image, LLMProvider, Part, Prompt, Text
from clarity_ai.schemas import DesignReview, PageUnderstanding, ReviewNote

MAX_NOTES = 12


class UnderstandingAgent:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    async def run(self, context: PageContext) -> Generated[PageUnderstanding]:
        parts: list[Part] = [_text_header(context)]
        if context.shots:
            first = context.shots[0]
            parts.append(Text(f"Screenshot: {first.label}"))
            parts.append(Image(first.data, first.media_type, label=first.label))
        parts.append(Text("Controls and headings:\n" + context.element_table()))
        prompt = Prompt(system=UNDERSTANDING_SYSTEM, parts=parts, max_tokens=4000, effort="low")
        return await self.provider.structured(prompt, PageUnderstanding)


class DesignReviewAgent:
    def __init__(self, provider: LLMProvider, *, max_notes: int = MAX_NOTES) -> None:
        self.provider = provider
        self.max_notes = max_notes

    async def run(
        self, context: PageContext, understanding: PageUnderstanding
    ) -> Generated[DesignReview]:
        system = DESIGN_REVIEW_SYSTEM.format(limit=self.max_notes, language=context.language_name)
        parts: list[Part] = [
            _text_header(context),
            Text(
                "What this page is for:\n"
                f"- kind: {understanding.kind.value}\n"
                f"- purpose: {understanding.purpose}\n"
                f"- audience: {understanding.audience}\n"
                f"- primary action: {understanding.primary_action or 'none identified'}"
                + (
                    f" (element #{understanding.primary_element})"
                    if understanding.primary_element is not None
                    else ""
                )
            ),
        ]
        for shot in context.shots:
            parts.append(Text(f"Screenshot: {shot.label}"))
            parts.append(Image(shot.data, shot.media_type, label=shot.label))
        parts.append(Text("Measured elements:\n" + context.element_table()))
        if context.signals:
            parts.append(
                Text("Other measurements:\n" + "\n".join(f"- {s}" for s in context.signals))
            )
        prompt = Prompt(system=system, parts=parts, max_tokens=16_000, effort="high")
        generated = await self.provider.structured(prompt, DesignReview)
        notes = sorted(generated.value.notes, key=_rank)[: self.max_notes]
        review = generated.value.model_copy(update={"notes": notes})
        return Generated(review, generated.model, generated.usage)


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "suggestion": 4}


def _rank(note: ReviewNote) -> tuple[int, float]:
    return SEVERITY_ORDER[note.severity], -note.confidence


def _text_header(context: PageContext) -> Text:
    return Text(
        f"Page: {context.title or '(untitled)'}\nURL: {context.url}\nOutline:\n{context.outline()}"
    )
