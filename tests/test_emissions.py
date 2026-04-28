"""
TestsÉmissions CO2
GET /emissions/stats
"""

import pytest


class TestEmissions:

    @pytest.mark.asyncio
    async def test_emissions_stats_status(self, client):
        """GET /emissions/stats retourne 200 ou 404 selon les données"""
        response = await client.get("/emissions/stats")
        assert response.status_code in (200, 404)
        if response.status_code == 404:
            data = response.json()
            assert data["message"] == "Ressource non trouvée"
            assert "Aucune donnée d'émission disponible" in data["detail"]

    @pytest.mark.asyncio
    async def test_emissions_stats_retourne_liste_ou_vide(self, client):
        """GET /emissions/stats retourne une liste ou une erreur 404"""
        response = await client.get("/emissions/stats")
        if response.status_code == 200:
            assert isinstance(response.json(), list)
        else:
            data = response.json()
            assert data["message"] == "Ressource non trouvée"

    @pytest.mark.asyncio
    async def test_emissions_stats_champs_requis_si_liste(self, client):
        """GET /emissions/stats retourne les bons champs si liste non vide"""
        response = await client.get("/emissions/stats")
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            assert "nb_trajets" in data
            assert "emission_moyenne_kg" in data

    @pytest.mark.asyncio
    async def test_emissions_stats_nb_trajets_positif_si_liste(self, client):
        """GET /emissions/stats retourne des nb_trajets >= 0 si liste non vide"""
        response = await client.get("/emissions/stats")
        if response.status_code == 200:
            for stat in response.json():
                assert stat["nb_trajets"] >= 0
