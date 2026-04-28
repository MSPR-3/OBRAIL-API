import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient
from main_v3 import app

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture()
async def client():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac