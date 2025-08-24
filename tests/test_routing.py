import pytest
from fastapi import status

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def _init_routes(radixer_app):
    @radixer_app.get("/health")
    async def health():
        return {"status": "ok"}

    @radixer_app.get("/users/{user_id}")
    async def get_user(user_id: int):
        return {"user_id": user_id}

    @radixer_app.get("/users/me")
    async def get_current_user():
        return {"user": "current"}

    @radixer_app.get("/users/{user_id}/posts/{post_id}")
    async def get_user_post(user_id: int, post_id: int):
        return {"user_id": user_id, "post_id": post_id}

    @radixer_app.get("/api/v1/status")
    async def api_status():
        return {"api": "v1", "status": "active"}

    @radixer_app.get("/api/v1/info")
    async def api_info():
        return {"api": "v1", "info": "data"}

    @radixer_app.post("/users")
    async def create_user():
        return {"created": True}

    @radixer_app.get("/categories/{name}")
    async def get_category(name: str):
        return {"category": name}

    @radixer_app.get("/")
    async def root():
        return {"message": "root"}


async def test_static_route_matching(client):
    response = await client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}


async def test_parameter_route_matching(client):
    response = await client.get("/users/123")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"user_id": 123}

    response = await client.get("/categories/electronics")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"category": "electronics"}


async def test_static_route_priority_over_param(client):
    # Static route should match
    response = await client.get("/users/me")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"user": "current"}

    # Parameter route should still work for other values
    response = await client.get("/users/456")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"user_id": 456}


async def test_multiple_parameters(client):
    response = await client.get("/users/123/posts/789")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"user_id": 123, "post_id": 789}


async def test_nested_static_routes(client):
    response = await client.get("/api/v1/status")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"api": "v1", "status": "active"}

    response = await client.get("/api/v1/info")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"api": "v1", "info": "data"}


async def test_http_method_matching(client):
    # GET should work
    response = await client.get("/users/123")
    assert response.status_code == status.HTTP_200_OK

    # POST should work on different endpoint
    response = await client.post("/users")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"created": True}

    # Wrong method should fail
    response = await client.post("/health")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


async def test_root_route(client):
    response = await client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "root"}


async def test_route_not_found(client):
    response = await client.get("/nonexistent")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_invalid_parameter_type(client):
    # Invalid int parameter should return validation error
    response = await client.get("/users/not-a-number")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Valid int parameter should work
    response = await client.get("/users/123")
    assert response.status_code == status.HTTP_200_OK


async def test_empty_path_segments(client):
    # Double slash should not match
    response = await client.get("/users//123")
    assert response.status_code == status.HTTP_404_NOT_FOUND
