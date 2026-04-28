"""
Tests: Imports ETL
GET /imports
"""

import pytest


class TestImports:

    @pytest.mark.asyncio
    async def test_imports_status_200(self, client):
        """GET /imports retourne 200"""
        response = await client.get("/imports")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_imports_retourne_liste(self, client):
        """GET /imports retourne une liste"""
        response = await client.get("/imports")
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_imports_filtre_statut_succes(self, client):
        """GET /imports?statut=succès retourne 200"""
        response = await client.get("/imports?statut=succès")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_imports_filtre_statut_echec(self, client):
        """GET /imports?statut=echec retourne 200"""
        response = await client.get("/imports?statut=echec")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_imports_filtre_statut_partiel(self, client):
        """GET /imports?statut=partiel retourne 200"""
        response = await client.get("/imports?statut=partiel")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_imports_statut_invalide(self, client):
        """GET /imports?statut=invalide retourne 400"""
        response = await client.get("/imports?statut=invalide")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_imports_pagination_limit(self, client):
        """GET /imports?limit=5 retourne au max 5 imports"""
        response = await client.get("/imports?limit=5")
        assert response.status_code == 200
        assert len(response.json()) <= 5

    @pytest.mark.asyncio
    async def test_imports_limit_zero(self, client):
        """GET /imports?limit=0 retourne 422"""
        response = await client.get("/imports?limit=0")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_imports_champs_requis(self, client):
        """GET /imports retourne les bons champs"""
        response = await client.get("/imports")
        if response.json():
            data = response.json()[0]
            assert "id_import" in data
            assert "date_import" in data
            assert "statut" in data
            assert "nb_lignes_importees" in data

    @pytest.mark.asyncio
    async def test_imports_nb_lignes_positif(self, client):
        """GET /imports retourne des nb_lignes_importees >= 0"""
        response = await client.get("/imports")
        for imp in response.json():
            assert imp["nb_lignes_importees"] >= 0
