#!/usr/bin/env python

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import prompt_api_router
from config import Config
import uvicorn

import sys
import logging
from pythonjsonlogger.json import JsonFormatter
from contextlib import asynccontextmanager


# Configure JSON logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(JsonFormatter())
handler.setLevel(logging.INFO)

logger.addHandler(handler)

# Load configuration
config = Config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting prompt API service...")
    app.state.db_path = config.db_path
    app.state.config = config
    logger.info(f"Database path set to: {app.state.db_path}")
    logger.info(f"Service running on port: {config.port}")

    yield

    # Shutdown
    logger.info("Shutting down prompt API service...")


app = FastAPI(
    title="Prompt Service API",
    description="HTTP API for managing prompts and plans",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(prompt_api_router, tags=["prompt_api"])


def main():
    uvicorn.run(app, host="0.0.0.0", port=int(config.port))


if __name__ == "__main__":
    main()
