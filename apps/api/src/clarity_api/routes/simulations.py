import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from clarity_api.deps import CurrentUser, Queue, Session
from clarity_persistence.models import FindingRecord, RunStatus, Simulation
from clarity_persistence.repositories import SimulationRepository

router = APIRouter(tags=["simulations"])


class SimulationOut(BaseModel):
    id: uuid.UUID
    finding_id: uuid.UUID
    status: RunStatus
    patch: dict[str, Any] | None
    result: dict[str, Any] | None
    error: str | None
    created_at: datetime

    @classmethod
    def of(cls, simulation: Simulation) -> "SimulationOut":
        return cls.model_validate(simulation, from_attributes=True)


@router.post("/findings/{finding_id}/simulations", status_code=status.HTTP_202_ACCEPTED)
async def simulate(
    finding_id: uuid.UUID, db: Session, queue: Queue, _: CurrentUser
) -> SimulationOut:
    finding = await db.get(FindingRecord, finding_id)
    if finding is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "finding not found")
    if not (finding.data.get("anchor") or {}).get("selector"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "the finding has no element")
    simulation = await SimulationRepository(db).create(finding)
    await db.commit()
    await db.refresh(simulation)
    await queue.enqueue_simulation(simulation.id)
    return SimulationOut.of(simulation)


@router.get("/findings/{finding_id}/simulations")
async def list_simulations(
    finding_id: uuid.UUID, db: Session, _: CurrentUser
) -> list[SimulationOut]:
    return [SimulationOut.of(s) for s in await SimulationRepository(db).for_finding(finding_id)]


@router.get("/simulations/{simulation_id}")
async def get_simulation(simulation_id: uuid.UUID, db: Session, _: CurrentUser) -> SimulationOut:
    simulation = await SimulationRepository(db).get(simulation_id)
    if simulation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "simulation not found")
    return SimulationOut.of(simulation)
