"""
Tests: Localisations
GET /localisations
"""

import pytest


class TestLocalisations:

    @pytest.mark.asyncio
    async def test_localisations_status_200(self, client):
        """GET /localisations retourne 200"""
        response = await client.get("/localisations")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_localisations_retourne_liste(self, client):
        """GET /localisations retourne une liste"""
        response = await client.get("/localisations")
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_localisations_filtre_code_pays(self, client):
        """GET /localisations?code_pays=FR retourne 200"""
        response = await client.get("/localisations?code_pays=FR")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_localisations_code_pays_invalide(self, client):
        """GET /localisations?code_pays=FRANCE retourne 400"""
        response = await client.get("/localisations?code_pays=FRANCE")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_localisations_champs_requis(self, client):
        """GET /localisations retourne les bons champs"""
        response = await client.get("/localisations")
        if response.json():
            data = response.json()[0]
            assert "code_pays" in data
            assert "nom_pays" in data
            assert "ville" in data

    @pytest.mark.asyncio
    async def test_localisations_code_pays_minuscule(self, client):
        """GET /localisations?code_pays=fr retourne 200"""
        response = await client.get("/localisations?code_pays=fr")
        assert response.status_code == 200
