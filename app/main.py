from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import research, history
from app.database import engine
from app import models

# Tạo bảng tự động
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Market Research Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(research.router, prefix="/api", tags=["Research"])
app.include_router(history.router, prefix="/api", tags=["History"])

@app.get("/")
def root():
    return {"message": "Market Research Agent đang chạy"}