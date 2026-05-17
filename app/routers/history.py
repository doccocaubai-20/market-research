from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Report
import json

router = APIRouter()

@router.get("/history")
def get_history(db: Session = Depends(get_db)):
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "topic": r.topic,
            "created_at": r.created_at.strftime("%d/%m/%Y %H:%M")
        }
        for r in reports
    ]

@router.get("/history/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return {"error": "Không tìm thấy báo cáo"}
    return {
        "id": report.id,
        "topic": report.topic,
        "report": report.report,
        "trends": report.trends,
        "competitors": report.competitors,
        "sources": json.loads(report.sources) if report.sources else [],
        "created_at": report.created_at.strftime("%d/%m/%Y %H:%M")
    }

@router.delete("/history/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if report:
        db.delete(report)
        db.commit()
    return {"message": "Đã xóa"}