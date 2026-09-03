from app.ai.llm import _openai_models


def test_openai_models_never_use_gemini_ids(monkeypatch):
    monkeypatch.setenv("AI_MODEL", "gemini-3.6-flash")
    models = _openai_models()
    assert models
    assert all(not model.lower().startswith("gemini") for model in models)
    assert "gpt-4o-mini" in models
