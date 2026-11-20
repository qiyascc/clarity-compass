from typing import Any

from pydantic import BaseModel

from clarity_ai.agents import (
    DesignReviewAgent,
    RecommendationAgent,
    SimulationAgent,
    UnderstandingAgent,
)
from clarity_ai.context import ElementLine, PageContext, Shot
from clarity_ai.provider import Generated, Image, Prompt, Text
from clarity_ai.schemas import (
    DesignPatch,
    DesignReview,
    NoteSeverity,
    PageKind,
    PageUnderstanding,
    PriorityItem,
    ReviewNote,
    Scores,
    SiteAssessment,
)


class ScriptedProvider:
    name = "scripted"
    model = "scripted-1"

    def __init__(self, reply: BaseModel) -> None:
        self.reply = reply
        self.prompts: list[Prompt] = []

    async def structured(self, prompt: Prompt, schema: type[Any]) -> Generated[Any]:
        self.prompts.append(prompt)
        assert isinstance(self.reply, schema)
        return Generated(self.reply, self.model)


CONTEXT = PageContext(
    url="https://theqiyas.cc/listing/1",
    title="Listing 1",
    notes_language="az",
    headings=["2-room flat, Nizami"],
    elements=[
        ElementLine(
            1, "desktop", "a", "button", "Contact agent", 40, 2210, 180, 44, attention=0.004
        ),
        ElementLine(2, "desktop", "p", None, "185 000 AZN", 40, 300, 200, 30, contrast=1.6),
    ],
    shots=[Shot("desktop section 1", b"one"), Shot("desktop section 2", b"two")],
    signals=["2 console errors"],
)

UNDERSTANDING = PageUnderstanding(
    kind=PageKind.LISTING_DETAIL,
    purpose="Show one flat for sale and get the visitor to contact the agent.",
    audience="People looking to buy a flat in Baku",
    primary_action="Contact the agent",
    primary_element=1,
    site_language="en",
)


def note(severity: NoteSeverity, confidence: float, title: str) -> ReviewNote:
    return ReviewNote(
        element=1,
        viewport="desktop",
        category="conversion",
        severity=severity,
        confidence=confidence,
        title=title,
        description="d",
        recommendation="r",
        alternative=None,
        evidence="desktop section 2",
    )


async def test_understanding_uses_only_the_first_screen_at_low_effort() -> None:
    provider = ScriptedProvider(UNDERSTANDING)
    result = await UnderstandingAgent(provider).run(CONTEXT)
    assert result.value.kind is PageKind.LISTING_DETAIL
    prompt = provider.prompts[0]
    assert prompt.effort == "low"
    assert [part.label for part in prompt.parts if isinstance(part, Image)] == ["desktop section 1"]


async def test_review_prompt_carries_purpose_language_evidence_and_rules() -> None:
    review = DesignReview(
        overall="o",
        strengths=[],
        scores=Scores(visual=70, ux=60, content=65, conversion=40, accessibility=50),
        notes=[note("low", 0.9, "c"), note("critical", 0.6, "a"), note("critical", 0.8, "b")],
    )
    provider = ScriptedProvider(review)
    result = await DesignReviewAgent(provider, max_notes=2).run(CONTEXT, UNDERSTANDING)

    assert [n.title for n in result.value.notes] == ["b", "a"]
    prompt = provider.prompts[0]
    assert prompt.effort == "high"
    assert "Azerbaijani" in prompt.system
    assert "Never state that a control is broken" in prompt.system
    text = "\n".join(part.text for part in prompt.parts if isinstance(part, Text))
    assert "kind: listing_detail" in text
    assert "(element #1)" in text
    assert '#1 | desktop | button | "Contact agent"' in text
    assert "contrast 1.60:1" in text
    assert "- 2 console errors" in text
    assert len([part for part in prompt.parts if isinstance(part, Image)]) == 2


def test_review_schema_has_no_functional_category() -> None:
    schema = ReviewNote.model_json_schema()
    assert "functional" not in schema["properties"]["category"]["enum"]


async def test_recommendations_drop_unknown_finding_numbers() -> None:
    reply = SiteAssessment(
        assessment="Solid but quiet.",
        strengths=["Fast"],
        priorities=[
            PriorityItem(
                title="Raise text contrast",
                why="w",
                action="a",
                impact="high",
                effort="small",
                findings=[1, 2, 9],
            )
        ],
    )
    provider = ScriptedProvider(reply)
    result = await RecommendationAgent(provider).run(
        "https://theqiyas.cc/", "ru", ["/ (home): fine"], ["[high verified] a", "[low predicted] b"]
    )
    assert result.value.priorities[0].findings == [1, 2]
    prompt = provider.prompts[0]
    assert "Russian" in prompt.system
    text = "\n".join(part.text for part in prompt.parts if isinstance(part, Text))
    assert "2. [low predicted] b" in text


async def test_simulation_prompt_names_the_target_and_language() -> None:
    patch = DesignPatch(css="#cta { background: #0f766e; }", changes=[], explanation="Darker CTA.")
    provider = ScriptedProvider(patch)
    result = await SimulationAgent(provider).run(
        "Contact button is hard to see", b"jpeg", ["#1 | a#cta | Contact"], 1, "tr"
    )
    assert result.value.css.startswith("#cta")
    prompt = provider.prompts[0]
    assert "Turkish" in prompt.system
    assert any(isinstance(p, Text) and "element #1" in p.text for p in prompt.parts)
    assert any(isinstance(p, Image) for p in prompt.parts)
