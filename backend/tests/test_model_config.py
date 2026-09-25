import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.config import LLM_MODEL, GEMINI_API_VERSION, get_genai_client, verify_llm_connection
from app.database import get_db
from app.main import app

def test_config_values():
    assert LLM_MODEL is not None and len(LLM_MODEL) > 0
    assert GEMINI_API_VERSION == "v1beta"
    client = get_genai_client()
    assert client is not None

def test_verify_llm_connection_failure():
    with patch.dict(os.environ, {"LLM_MODEL": "invalid-model-name-for-test"}):
        with patch("app.config.get_genai_client") as mock_client_factory:
            mock_client = MagicMock()
            mock_client.models.generate_content.side_effect = Exception("Model not found")
            mock_client_factory.return_value = mock_client
            with pytest.raises(RuntimeError) as exc_info:
                verify_llm_connection()
            assert "CRITICAL: LLM startup health check failed" in str(exc_info.value)

@patch("time.sleep", return_value=None)
@patch("app.main.verify_llm_connection", return_value=None)
def test_upload_llm_failure_returns_llm_unavailable(mock_verify, mock_sleep):
    with patch("app.api.endpoints.get_genai_client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("503 UNAVAILABLE")
        mock_client_factory.return_value = mock_client
        
        with TestClient(app) as client:
            files = {"file": ("test.docx", b"PK\x03\x04dummy content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            with patch("app.api.endpoints.extract_text_from_document", return_value="Clause 1 text"):
                with patch("app.api.endpoints.chunk_text", return_value=[{"chunk_id": 1, "text": "Clause 1 text"}]):
                    with patch("app.api.endpoints.store_chunks"):
                        resp = client.post("/api/upload", files=files, data={"target_language": "en"})
                        assert resp.status_code == 503
                        data = resp.json()
                        assert data["detail"]["error_code"] == "llm_unavailable"
                        assert data["detail"]["message"] == "Something went wrong on our end, please try again."

@patch("time.sleep", return_value=None)
@patch("app.main.verify_llm_connection", return_value=None)
def test_summary_llm_failure_returns_llm_unavailable(mock_verify, mock_sleep):
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.summary = None
    mock_doc.clauses = [{"id": "1", "risk": "flag", "original": "text", "simplified": "simp", "explanation": "exp"}]
    mock_doc.target_language = "en"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_doc

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with patch("app.api.endpoints.get_genai_client") as mock_client_factory:
            mock_client = MagicMock()
            mock_client.models.generate_content.side_effect = Exception("503 UNAVAILABLE")
            mock_client_factory.return_value = mock_client

            with TestClient(app) as client:
                resp = client.get("/api/documents/test-id/summary")
                assert resp.status_code == 503
                data = resp.json()
                assert data["detail"]["error_code"] == "llm_unavailable"
                assert data["detail"]["message"] == "Something went wrong on our end, please try again."
    finally:
        app.dependency_overrides.pop(get_db, None)

