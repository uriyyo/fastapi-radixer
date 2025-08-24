import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from fastapi_radixer import Radixer, init_app


@pytest.fixture
def app() -> FastAPI:
    return FastAPI()


@pytest.fixture
def radixer() -> Radixer:
    return Radixer()


@pytest.fixture
def radixer_app(app, radixer) -> FastAPI:
    init_app(app, radixer=radixer)
    return app


@pytest_asyncio.fixture
async def client(app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app),
        base_url="http://testserver",
        timeout=60,
    ) as c:
        yield c
