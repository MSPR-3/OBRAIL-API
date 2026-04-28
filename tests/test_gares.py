"""
Tests: Gares
GET /gares
GET /gares/{id_gare}
"""

import pytest


class TestGaresListe:

    @pytest.mark.asyncio
    async def test_gares_status(self, client):
        """GET /gares retourne 200 ou 404 selon les données"""
        response = await client.get("/gares")
        assert response.status_code in (200, 404)
        if response.status_code == 404:
            data = response.json()
            assert data["message"] == "Ressource non trouvée"
            assert "Erreur récupération gares" in data["detail"] or "Aucune gare trouvée" in data["detail"]

    @pytest.mark.asyncio
    async def test_gares_retourne_liste_ou_vide(self, client):
        """GET /gares retourne une liste ou une erreur 404"""
        response = await client.get("/gares")
        if response.status_code == 200:
            assert isinstance(response.json(), list)
        else:
            data = response.json()
            assert data["message"] == "Ressource non trouvée"

    @pytest.mark.asyncio
    async def test_gares_filtre_code_pays(self, client):
        """GET /gares?code_pays=FR retourne 200 ou 404"""
        response = await client.get("/gares?code_pays=FR")
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_gares_filtre_code_pays_de(self, client):
        """GET /gares?code_pays=DE retourne 200 ou 404"""
        response = await client.get("/gares?code_pays=DE")
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_gares_filtre_ville(self, client):
        """GET /gares?ville=Paris retourne 200 ou 404"""
        response = await client.get("/gares?ville=Paris")
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_gares_filtre_type_nationale(self, client):
        """GET /gares?type_liaison=nationale retourne 200 ou 404"""
        response = await client.get("/gares?type_liaison=nationale")
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_gares_filtre_type_internationale(self, client):
        """GET /gares?type_liaison=internationale retourne 200 ou 404"""
        response = await client.get("/gares?type_liaison=internationale")
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_gares_filtre_type_regionale(self, client):
        """GET /gares?type_liaison=régionale retourne 200 ou 404"""
        response = await client.get("/gares?type_liaison=régionale")
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_gares_code_pays_minuscule(self, client):
        """GET /gares?code_pays=fr (minuscule) retourne 200"""
        response = await client.get("/gares?code_pays=fr")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_gares_pagination_limit(self, client):
        """GET /gares?limit=5 retourne au max 5 gares"""
        response = await client.get("/gares?limit=5")
        assert response.status_code == 200
        assert len(response.json()) <= 5

    @pytest.mark.asyncio
    async def test_gares_champs_requis(self, client):
        """GET /gares retourne les bons champs"""
        response = await client.get("/gares")
        if response.json():
            data = response.json()[0]
            assert "id_gare" in data
            assert "nom_officiel" in data
            assert "code_pays" in data
            assert "ville" in data
            assert "type_liaison" in data


class TestGaresErreurs:

    @pytest.mark.asyncio
    async def test_gares_code_pays_invalide(self, client):
        """GET /gares?code_pays=FRANCE retourne 400"""
        response = await client.get("/gares?code_pays=FRANCE")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_gares_type_liaison_invalide(self, client):
        """GET /gares?type_liaison=invalide retourne 400"""
        response = await client.get("/gares?type_liaison=invalide")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_gares_limit_zero(self, client):
        """GET /gares?limit=0 retourne 422"""
        response = await client.get("/gares?limit=0")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_gare_non_existante_404(self, client):
        """GET /gares/99999 retourne 404"""
        response = await client.get("/gares/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_gare_erreur_contient_detail(self, client):
        """GET /gares/99999 retourne un message d'erreur"""
        response = await client.get("/gares/99999")
        assert "detail" in response.json()


class TestGareDetail:

    @pytest.mark.asyncio
    async def test_gare_par_id_champs(self, client):
        """GET /gares/1 retourne les bons champs si la gare existe"""
        response = await client.get("/gares/1")
        if response.status_code == 200:
            data = response.json()
            assert "id_gare" in data
            assert "nom_officiel" in data
            assert "code_pays" in data
            assert "ville" in data
