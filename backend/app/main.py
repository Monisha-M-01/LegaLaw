import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router
from app.config import verify_llm_connection, LLM_MODEL, GEMINI_API_VERSION
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ai_legal_assistant")

async def _run_startup_health_check():
    """Run the external LLM check without blocking the API from accepting requests."""
    try:
        await asyncio.to_thread(verify_llm_connection)
        logger.info("Startup LLM health check passed.")
    except RuntimeError as e:
        logger.critical(
            f"LLM health check failed at startup: {e}\n"
            "The API is available, but LLM-backed requests may fail until the LLM API recovers."
        )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the health check in the background so external LLM latency cannot
    # prevent uvicorn from binding the API port.
    logger.info(f"Starting AI Legal Assistant API with model '{LLM_MODEL}' (API version: '{GEMINI_API_VERSION}')...")
    health_check_task = asyncio.create_task(_run_startup_health_check())
    logger.info("Startup complete. API is ready to accept requests.")
    yield
    health_check_task.cancel()
    logger.info("Shutting down AI Legal Assistant API.")

app = FastAPI(
    title="AI Legal Assistant API",
    description="API for the AI-powered legal assistant hackathon project.",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the AI Legal Assistant API",
        "model": LLM_MODEL,
        "api_version": GEMINI_API_VERSION,
        "status": "healthy"
    }
