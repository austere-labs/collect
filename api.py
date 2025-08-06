#!/usr/bin/env python

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import prompt_api_router
from config import Config
import uvicorn

import sys
import logging
from pythonjsonlogger import jsonlogger
from contextlib import asynccontextmanager

# Module-level logger configuration
logger = logging.getLogger("prompt_api")
logger.setLevel(logging.DEBUG)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
stdout_handler.setLevel(logging.DEBUG)

fmt = jsonlogger.JsonFormatter(
    "%(name)s %(asctime)s %(levelname)s %(filename)s %(lineno)s %(process)d %(message)s",
    rename_fields={"levelname": "severity", "asctime": "timestamp"},
)
stdout_handler.setFormatter(fmt)
logger.addHandler(stdout_handler)

# Load configuration
config = Config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting prompt API service...")
    app.state.db_path = config.db_path if hasattr(
        config, 'db_path') else "data/collect.db"
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
    lifespan=lifespan
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
