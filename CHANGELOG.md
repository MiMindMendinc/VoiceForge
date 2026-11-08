# Changelog

All notable changes to VoiceForge are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-11-08

### Added

- OpenAI-compatible `POST /v1/audio/speech` (`input`, `voice`, `speed`, `response_format`, `model`)
- OpenAI voice aliases: `alloy` → `af_heart`, `echo` → `am_adam`, `fable` → `bm_george`, `onyx` → `am_michael`, `nova` → `af_bella`, `shimmer` → `af_sarah`
- `POST /speak/stream` sentence-by-sentence SSE (base64 WAV clips, then `done` or `error`)
- Optional MP3 and Opus output through system FFmpeg (`libmp3lame` / `libopus`); missing encoders return HTTP 503
- `voiceforge` CLI: `serve`, `download`, `--check`, `--force`, and `--no-download`
- `pyproject.toml` packaging so you can run `pip install -e .` then `voiceforge serve`
- CPU `Dockerfile` with FFmpeg, no baked-in model files, models mounted at `/app/models`
- [SECURITY.md](SECURITY.md) describing the local-first defaults and how to report issues
- [docs/LLM.md](docs/LLM.md) copy-paste setups for Ollama, llama.cpp, and Open WebUI
- [CONTRIBUTING.md](CONTRIBUTING.md) and GitHub issue templates for bugs and features
- [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for Kokoro (Apache 2.0) and kokoro-onnx (MIT)

### Changed

- Health endpoint and package version are now `1.2.0`
- Runtime and test dependency pins refreshed (including Uvicorn, kokoro-onnx, SoundFile, Pydantic, HTTPX, and Ruff)
- README documents `voiceforge serve`, the OpenAI speech API, streaming, Docker, and the LLM hookup guide

## [1.1.0] - 2026-11-08

### Added

- First standalone VoiceForge repository, imported from the Agent-Reach draft
- Local FastAPI server with `POST /speak`, `GET /voices`, and `GET /health`
- Kokoro-ONNX engine, demo page, Python and JavaScript clients
- Model downloader with SHA-256 checks
- Pytest suite, JavaScript client tests, and GitHub Actions CI
