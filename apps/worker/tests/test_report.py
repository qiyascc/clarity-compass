from typing import Any

from clarity_ai.agents import RecommendationAgent
from clarity_ai.provider import Generated, Prompt
from clarity_ai.schemas import PriorityItem, SiteAssessment
from clarity_core.domain.findings import Category, Finding, Severity, Status
from clarity_core.domain.viewport import Viewport
from clarity_worker.report import build_report


class ScriptedProvider:
    name = "scripted"
    model = "scripted-1"

    def __init__(self) -> None:
        self.prompts: list[Prompt] = []

    async def structured(self, prompt: Prompt, schema: type[Any]) -> Generated[Any]:
        self.prompts.append(prompt)
        return Generated(
            SiteAssessment(
                assessment="Clean site, weak calls to action.",
                strengths=["Fast pages"],
                priorities=[
                    PriorityItem(
                        title="Fix the dead search button",
                        why="w",
                        action="a",
                        impact="high",
                        effort="small",
                        findings=[1],
                    )
                ],
            ),
            self.model,
        )


def finding(severity: Severity, title: str) -> Finding:
    return Finding(
        page_url="https://shop.test/",
        viewport=Viewport.DESKTOP,
        category=Category.UX,
        severity=severity,
        status=Status.PREDICTED,
        confidence=0.5,
        title=title,
        description="d",
        recommendation="r",
    )


async def test_plan_items_reference_ranked_findings() -> None:
    low, critical = finding(Severity.LOW, "minor"), finding(Severity.CRITICAL, "dead search")
    provider = ScriptedProvider()
    report = await build_report(
        "https://shop.test/", "en", [low, critical], {}, RecommendationAgent(provider)
    )
    assert report.assessment == "Clean site, weak calls to action."
    assert report.priorities[0].finding_ids == [str(critical.id)]
    assert report.totals["findings"] == 2


async def test_report_without_a_model_is_still_built() -> None:
    report = await build_report("https://shop.test/", "en", [finding(Severity.HIGH, "x")], {}, None)
    assert report.assessment is None
    assert report.by_severity == {"high": 1}
