"""
Tests: Racine de l'API
GET /
"""

import pytest


class TestRacine:

    @pytest.mark.asyncio
    async def test_root_status_200(self, client):
        """La racine retourne 200"""
        response = await client.get("/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_root_contient_api(self, client):
        """La racine contient le nom de l'API"""
        response = await client.get("/")
        assert response.json()["api"] == "ObRail Europe"

    @pytest.mark.asyncio
    async def test_root_contient_version(self, client):
        """La racine contient la version"""
        response = await client.get("/")
        assert "version" in response.json()

    @pytest.mark.asyncio
    async def test_root_contient_endpoints(self, client):
        """La racine liste les endpoints disponibles"""
        response = await client.get("/")
        assert "endpoints" in response.json()
        assert len(response.json()["endpoints"]) > 0

    @pytest.mark.asyncio
    async def test_root_contient_documentation(self, client):
        """La racine contient le lien vers la documentation"""
        response = await client.get("/")
        assert "documentation" in response.json()

    @pytest.mark.asyncio
    async def test_route_inexistante_404(self, client):
        """Une route inexistante retourne 404"""
        response = await client.get("/route_inexistante")
        assert response.status_code == 404
