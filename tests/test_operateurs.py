"""
Tests: Opérateurs
GET /operateurs
"""

import pytest


class TestOperateurs:

    @pytest.mark.asyncio
    async def test_operateurs_status_200(self, client):
        """GET /operateurs retourne 200"""
        response = await client.get("/operateurs")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_operateurs_retourne_liste(self, client):
        """GET /operateurs retourne une liste"""
        response = await client.get("/operateurs")
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_operateurs_champs_requis(self, client):
        """GET /operateurs retourne les bons champs"""
        response = await client.get("/operateurs")
        if response.json():
            data = response.json()[0]
            assert "id_operateur" in data
            assert "nom" in data
            assert "nb_trajets" in data

    @pytest.mark.asyncio
    async def test_operateurs_tries_par_nb_trajets(self, client):
        """GET /operateurs retourne les opérateurs triés par nb_trajets décroissant"""
        response = await client.get("/operateurs")
        if len(response.json()) > 1:
            trajets = [o["nb_trajets"] for o in response.json()]
            assert trajets == sorted(trajets, reverse=True)

    @pytest.mark.asyncio
    async def test_operateurs_nb_trajets_positif(self, client):
        """GET /operateurs retourne des nb_trajets >= 0"""
        response = await client.get("/operateurs")
        for op in response.json():
            assert op["nb_trajets"] >= 0
