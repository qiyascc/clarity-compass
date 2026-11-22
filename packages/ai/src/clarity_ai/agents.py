from clarity_ai.context import LANGUAGE_NAMES, PageContext
from clarity_ai.prompts import (
    DESIGN_REVIEW_SYSTEM,
    SIMULATION_SYSTEM,
    SYNTHESIS_SYSTEM,
    UNDERSTANDING_SYSTEM,
)
from clarity_ai.provider import Generated, Image, LLMProvider, Part, Prompt, Text
from clarity_ai.schemas import (
    DesignPatch,
    DesignReview,
    PageUnderstanding,
    ReviewNote,
    SiteAssessment,
)

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


class RecommendationAgent:
    def __init__(self, provider: LLMProvider, *, max_items: int = 8) -> None:
        self.provider = provider
        self.max_items = max_items

    async def run(
        self, site: str, language: str, pages: list[str], findings: list[str]
    ) -> Generated[SiteAssessment]:
        system = SYNTHESIS_SYSTEM.format(
            limit=self.max_items, language=LANGUAGE_NAMES.get(language, "English")
        )
        numbered = "\n".join(f"{number}. {line}" for number, line in enumerate(findings, 1))
        prompt = Prompt(
            system=system,
            parts=[
                Text(f"Site: {site}"),
                Text("Pages:\n" + ("\n".join(pages) or "(no page reviews)")),
                Text("Findings:\n" + (numbered or "(none)")),
            ],
            # Thinking shares this budget; non-streaming calls are capped near 21k.
            max_tokens=20_000,
            effort="high",
        )
        generated = await self.provider.structured(prompt, SiteAssessment)
        plan = generated.value.priorities[: self.max_items]
        valid = range(1, len(findings) + 1)
        cleaned = [
            item.model_copy(update={"findings": [n for n in item.findings if n in valid]})
            for item in plan
        ]
        assessment = generated.value.model_copy(update={"priorities": cleaned})
        return Generated(assessment, generated.model, generated.usage)


class SimulationAgent:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    async def run(
        self,
        finding: str,
        screenshot: bytes,
        elements: list[str],
        target: int,
        language: str,
    ) -> Generated[DesignPatch]:
        system = SIMULATION_SYSTEM.format(language=LANGUAGE_NAMES.get(language, "English"))
        prompt = Prompt(
            system=system,
            parts=[
                Text(f"Finding:\n{finding}"),
                Text(f"The finding is about element #{target}."),
                Image(screenshot, label="current screen"),
                Text("Elements on this screen:\n" + "\n".join(elements)),
            ],
            max_tokens=8_000,
            effort="medium",
        )
        return await self.provider.structured(prompt, DesignPatch)


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "suggestion": 4}


def _rank(note: ReviewNote) -> tuple[int, float]:
    return SEVERITY_ORDER[note.severity], -note.confidence


def _text_header(context: PageContext) -> Text:
    return Text(
        f"Page: {context.title or '(untitled)'}\nURL: {context.url}\nOutline:\n{context.outline()}"
    )
