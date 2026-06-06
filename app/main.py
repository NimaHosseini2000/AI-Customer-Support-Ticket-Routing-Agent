from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402

import app.models  # noqa: F401, E402  — registers ORM models with Base before create_all
from app.database import Base, engine  # noqa: E402
from app.routes import tickets  # noqa: E402

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Customer Support Agent",
    description="AI-powered customer support ticket routing and classification",
    version="1.0.0",
)

app.include_router(tickets.router)
