from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.agents.orchestrator import run
from app.database import get_db, SessionLocal
from app.models import Report
import json
import asyncio
from queue import Queue
from threading import Thread
router = APIRouter()

class ResearchRequest(BaseModel):
    topic: str

@router.post("/research")
async def research(request: ResearchRequest, db: Session = Depends(get_db)):

    result = await run(request.topic)
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


@router.get("/research/stream")
def research_stream(topic: str):
    if not topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")

    def stream():
        queue: Queue = Queue()

        def callback(event: dict):
            queue.put({"type": "progress", "data": event})

        def worker():
            db = SessionLocal()
            try:
                # Run the async orchestrator in this worker thread.
                result = asyncio.run(run(topic, callback))
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
                queue.put({"type": "done", "data": result})
            except Exception as exc:
                queue.put({"type": "error", "data": {"message": str(exc)}})
            finally:
                db.close()
                queue.put(None)

        Thread(target=worker, daemon=True).start()

        while True:
            item = queue.get()
            if item is None:
                break
            payload = json.dumps(item["data"], ensure_ascii=False)
            yield f"event: {item['type']}\ndata: {payload}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
