"""
Test per gli endpoint REST di gestione dei preventivi.

Copre i due nuovi endpoint:
  GET    /api/preventivi          → lista preventivi
  DELETE /api/preventivo/{id}     → elimina preventivo
"""

import json
import pytest
from fastapi.testclient import TestClient

import cbd_preventivi.api.routes as routes_module
from cbd_preventivi.api.app import app
from cbd_preventivi.models import Preventivo


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Client con DATA_DIR isolata in tmp_path."""
    monkeypatch.setattr(routes_module, "DATA_DIR", tmp_path)
    return TestClient(app)


def _scrivi_preventivo(tmp_path, id_: str, nome: str = "", data: str = "") -> None:
    prev = Preventivo(id=id_, nome=nome, data=data)
    (tmp_path / f"{id_}.json").write_text(prev.model_dump_json())


# ---------------------------------------------------------------------------
# GET /api/preventivi
# ---------------------------------------------------------------------------

class TestListaPreventivi:
    def test_lista_vuota(self, client):
        r = client.get("/api/preventivi")
        assert r.status_code == 200
        assert r.json() == []

    def test_lista_con_preventivi(self, client, tmp_path):
        _scrivi_preventivo(tmp_path, "aaa", nome="Bagno Rossi", data="10/05/2026")
        _scrivi_preventivo(tmp_path, "bbb", nome="Cucina Bianchi", data="02/05/2026")
        r = client.get("/api/preventivi")
        assert r.status_code == 200
        ids = [p["id"] for p in r.json()]
        assert set(ids) == {"aaa", "bbb"}
        for p in r.json():
            assert "id" in p and "nome" in p and "data" in p

    def test_file_corrotto_ignorato(self, client, tmp_path):
        _scrivi_preventivo(tmp_path, "buono", nome="Ok")
        (tmp_path / "corrotto.json").write_text("non è json valido")
        r = client.get("/api/preventivi")
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["id"] == "buono"


# ---------------------------------------------------------------------------
# DELETE /api/preventivo/{id}
# ---------------------------------------------------------------------------

class TestEliminaPreventivo:
    def test_elimina_esistente(self, client, tmp_path):
        _scrivi_preventivo(tmp_path, "del1", nome="Da eliminare")
        r = client.delete("/api/preventivo/del1")
        assert r.status_code == 204
        assert not (tmp_path / "del1.json").exists()

    def test_elimina_inesistente_404(self, client):
        r = client.delete("/api/preventivo/nonexist")
        assert r.status_code == 404
