from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.agents.orchestrator import run
from app.database import get_db
from app.models import Report
import json
router = APIRouter()

class ResearchRequest(BaseModel):
    topic: str

@router.post("/research")
async def research(request: ResearchRequest, db: Session = Depends(get_db)):
    
    result = run(request.topic)
    report = Report(
        topic=result["topic"],
        report=result["report"],
        trends=result["details"]["trends"],
        competitors=result["details"]["competitors"],
        sources=json.dumps(result["sources"], ensure_ascii=False)
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    result["id"] = report.id
    return result
