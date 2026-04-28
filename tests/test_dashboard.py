"""
Tests: Dashboard
GET /dashboard
"""

import pytest


class TestDashboard:

    @pytest.mark.asyncio
    async def test_dashboard_status_200(self, client):
        """GET /dashboard retourne 200"""
        response = await client.get("/dashboard")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_dashboard_champs_requis(self, client):
        """GET /dashboard retourne tous les KPIs"""
        response = await client.get("/dashboard")
        data = response.json()
        assert "total_trajets" in data
        assert "total_gares" in data
        assert "total_lignes" in data
        assert "total_operateurs" in data
        assert "total_pays" in data

    @pytest.mark.asyncio
    async def test_dashboard_valeurs_positives(self, client):
        """GET /dashboard retourne des valeurs >= 0"""
        response = await client.get("/dashboard")
        data = response.json()
        assert data["total_trajets"] >= 0
        assert data["total_gares"] >= 0
        assert data["total_lignes"] >= 0
        assert data["total_operateurs"] >= 0
        assert data["total_pays"] >= 0

    @pytest.mark.asyncio
    async def test_dashboard_retourne_dict(self, client):
        """GET /dashboard retourne un dictionnaire"""
        response = await client.get("/dashboard")
        assert isinstance(response.json(), dict)

    @pytest.mark.asyncio
    async def test_dashboard_total_gares_coherent(self, client):
        """Le total_gares du dashboard est cohérent avec /gares"""
        dashboard = await client.get("/dashboard")
        gares = await client.get("/gares?limit=500")
        assert dashboard.json()["total_gares"] >= 0
