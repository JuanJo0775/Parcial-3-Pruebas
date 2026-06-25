import os
import socket
import subprocess
import sys
import time
from pathlib import Path
import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB_DEFAULT_URL = "sqlite:///./ticketfast_test.db"
DATABASE_URL_TEST = os.getenv("DATABASE_URL", TEST_DB_DEFAULT_URL)
os.environ.setdefault("DATABASE_URL", DATABASE_URL_TEST)

from src.database.config import get_db  # noqa: E402
from src.database.models import Base  # noqa: E402
from src.reservas.api import app  # noqa: E402

ROOT_DIR = Path(__file__).resolve().parents[1]
USE_SQLITE = DATABASE_URL_TEST.startswith("sqlite")

engine = create_engine(
    DATABASE_URL_TEST,
    connect_args={"check_same_thread": False} if USE_SQLITE else {},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_api(base_url: str, timeout_seconds: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            response = httpx.get(f"{base_url}/openapi.json", timeout=1.0)
        except httpx.RequestError:
            response = None
        if response is not None and response.status_code == 200:
            return True
        time.sleep(0.25)
    return False


@pytest.fixture(scope="session", autouse=True)
def crear_tablas():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def base_url():
    process = None

    if USE_SQLITE:
        port = _find_free_port()
        base_url_value = f"http://127.0.0.1:{port}"
        env = os.environ.copy()
        env["DATABASE_URL"] = DATABASE_URL_TEST
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "src.reservas.api:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=ROOT_DIR,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if not _wait_for_api(base_url_value):
            process.terminate()
            process.wait(timeout=10)
            raise RuntimeError("No se pudo iniciar el servidor local de pruebas.")
    else:
        base_url_value = os.getenv("API_BASE_URL", "http://127.0.0.1:8001")

    yield base_url_value

    if process is not None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client_con_bd(db_session):
    def _get_db_override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
