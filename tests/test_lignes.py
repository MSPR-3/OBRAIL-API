"""
Tests: Lignes
GET /lignes
"""

import pytest


class TestLignes:

    @pytest.mark.asyncio
    async def test_lignes_status_200(self, client):
        """GET /lignes retourne 200"""
        response = await client.get("/lignes")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_lignes_retourne_liste(self, client):
        """GET /lignes retourne une liste"""
        response = await client.get("/lignes")
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_lignes_pagination_limit(self, client):
        """GET /lignes?limit=5 retourne au max 5 lignes"""
        response = await client.get("/lignes?limit=5")
        assert response.status_code == 200
        assert len(response.json()) <= 5

    @pytest.mark.asyncio
    async def test_lignes_pagination_offset(self, client):
        """GET /lignes?offset=0 retourne 200"""
        response = await client.get("/lignes?offset=0")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_lignes_champs_requis(self, client):
        """GET /lignes retourne les bons champs"""
        response = await client.get("/lignes")
        if response.json():
            data = response.json()[0]
            assert "id_ligne" in data
            assert "nom_ligne" in data

    @pytest.mark.asyncio
    async def test_lignes_limit_zero(self, client):
        """GET /lignes?limit=0 retourne 422"""
        response = await client.get("/lignes?limit=0")
        assert response.status_code == 422
