# Contributing to VoiceForge

Use Python 3.10+ and Node 18+ for JavaScript client tests. From the repository
root, activate your virtual environment and run:

```bash
pip install -r requirements-dev.txt
ruff check .
pytest tests -q
node --test clients/js/voiceforge.test.mjs
```

Tests use a fake speech engine; no model download is needed. The `voiceforge`
GitHub Actions workflow runs Python lint/tests on Python 3.10–3.13, JavaScript
tests on Node 20, plus `pip-audit` against pinned runtime/development requirements.

Fork this repository (or use a branch if you have write access), make a focused
change, run those checks, and open a pull request into `main`. Describe what
changed, why, and which checks you ran. Add/update tests for behavior changes
and keep examples consistent with the API. Do not commit model files,
generated audio, or credentials.
