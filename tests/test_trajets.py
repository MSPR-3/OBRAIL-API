"""
Tests: Trajets
GET /trajets
GET /trajets/{id_trajet}
"""

import pytest


class TestTrajetsListe:

    @pytest.mark.asyncio
    async def test_trajets_status(self, client):
        """GET /trajets retourne 200 ou 404 selon les données"""
        response = await client.get("/trajets")
        assert response.status_code in (200, 404)
        if response.status_code == 404:
            data = response.json()
            assert data["message"] == "Ressource non trouvée"
            assert "Erreur récupération trajets" in data["detail"] or "Aucun trajet trouvé" in data["detail"]

    @pytest.mark.asyncio
    async def test_trajets_retourne_liste_ou_vide(self, client):
        """GET /trajets retourne une liste ou une erreur 404"""
        response = await client.get("/trajets")
        if response.status_code == 200:
            assert isinstance(response.json(), list)
        else:
            data = response.json()
            assert data["message"] == "Ressource non trouvée"

    @pytest.mark.asyncio
    async def test_trajets_filtre_ville_depart(self, client):
        """GET /trajets?ville_depart=Paris retourne 200 ou 404"""
        response = await client.get("/trajets?ville_depart=Paris")
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_trajets_filtre_ville_arrivee(self, client):
        """GET /trajets?ville_arrivee=Berlin retourne 200 ou 404"""
        response = await client.get("/trajets?ville_arrivee=Berlin")
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_trajets_filtre_depart_et_arrivee(self, client):
        """GET /trajets avec ville_depart et ville_arrivee retourne 200 ou 404"""
        response = await client.get("/trajets?ville_depart=Paris&ville_arrivee=Berlin")
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_trajets_filtre_operateur(self, client):
        """GET /trajets?operateur=SNCF retourne 200 ou 404"""
        response = await client.get("/trajets?operateur=SNCF")
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_trajets_filtre_code_pays_depart(self, client):
        """GET /trajets?code_pays_depart=FR retourne 200 ou 404"""
        response = await client.get("/trajets?code_pays_depart=FR")
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_trajets_filtre_code_pays_arrivee(self, client):
        """GET /trajets?code_pays_arrivee=DE retourne 200 ou 404"""
        response = await client.get("/trajets?code_pays_arrivee=DE")
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_trajets_filtre_duree_max(self, client):
        """GET /trajets?duree_max=480 retourne 200"""
        response = await client.get("/trajets?duree_max=480")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_trajets_filtre_emission_max(self, client):
        """GET /trajets?emission_max=50 retourne 200"""
        response = await client.get("/trajets?emission_max=50")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_trajets_filtres_combines(self, client):
        """GET /trajets avec plusieurs filtres combinés retourne 200"""
        response = await client.get(
            "/trajets?ville_depart=Paris&code_pays_arrivee=DE&duree_max=600"
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_trajets_pagination_limit(self, client):
        """GET /trajets?limit=10 retourne au max 10 trajets"""
        response = await client.get("/trajets?limit=10")
        assert response.status_code == 200
        assert len(response.json()) <= 10

    @pytest.mark.asyncio
    async def test_trajets_pagination_offset(self, client):
        """GET /trajets?offset=0 retourne 200"""
        response = await client.get("/trajets?offset=0")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_trajets_champs_requis(self, client):
        """GET /trajets retourne les bons champs"""
        response = await client.get("/trajets")
        if response.json():
            data = response.json()[0]
            assert "id_trajet" in data
            assert "heure_depart" in data
            assert "heure_arrivee" in data
            assert "duree_minutes" in data


class TestTrajetsErreurs:

    @pytest.mark.asyncio
    async def test_trajets_limit_zero(self, client):
        """GET /trajets?limit=0 retourne 422"""
        response = await client.get("/trajets?limit=0")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_trajets_limit_trop_grand(self, client):
        """GET /trajets?limit=9999 retourne 422"""
        response = await client.get("/trajets?limit=9999")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_trajets_code_pays_invalide(self, client):
        """GET /trajets?code_pays_depart=FRANCE retourne 400"""
        response = await client.get("/trajets?code_pays_depart=FRANCE")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_trajets_duree_max_negative(self, client):
        """GET /trajets?duree_max=-1 retourne 422"""
        response = await client.get("/trajets?duree_max=-1")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_trajets_emission_max_negative(self, client):
        """GET /trajets?emission_max=-10 retourne 422"""
        response = await client.get("/trajets?emission_max=-10")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_trajet_id_non_existant(self, client):
        """GET /trajets/99999 retourne 404"""
        response = await client.get("/trajets/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_trajet_erreur_contient_detail(self, client):
        """GET /trajets/99999 retourne un message d'erreur"""
        response = await client.get("/trajets/99999")
        assert response.status_code == 404
        assert "detail" in response.json()


class TestTrajetDetail:

    @pytest.mark.asyncio
    async def test_trajet_par_id_champs(self, client):
        """GET /trajets/1 retourne les bons champs si le trajet existe"""
        response = await client.get("/trajets/1")
        if response.status_code == 200:
            data = response.json()
            assert "id_trajet" in data
            assert "heure_depart" in data
            assert "heure_arrivee" in data
            assert "duree_minutes" in data
