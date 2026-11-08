"""Compatibility, format and sentence-stream tests using only a fake engine."""
from __future__ import annotations

import base64
import io
import json
import shutil
import subprocess

import numpy as np
import pytest
import soundfile as sf
from voiceforge_fakes import FakeEngine

from server import VOICE_ALIASES, Settings, create_app
from tts.audio import EncoderError, encode_audio, split_sentences


def test_openai_wav(client, fake_engine):
    response = client.post("/v1/audio/speech", json={
        "input": " Hello LLM. ", "model": "tts-1", "voice": "nova", "speed": 1.25,
        "response_format": "wav",
    })
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.headers["cache-control"] == "no-store"
    audio, rate = sf.read(io.BytesIO(response.content))
    assert len(audio) > 0 and rate == 24000
    assert fake_engine.calls == [("Hello LLM.", "af_bella", 1.25)]


@pytest.mark.parametrize("alias,native", VOICE_ALIASES.items())
def test_voice_aliases(make_client, alias, native):
    engine = FakeEngine(voices=tuple(VOICE_ALIASES.values()))
    client = make_client(engine)
    assert client.post("/v1/audio/speech", json={"input": "Hello", "voice": alias}).status_code == 200
    assert engine.calls == [("Hello", native, 1.0)]


def test_native_voice_and_defaults(client, fake_engine):
    assert client.post("/v1/audio/speech", json={"input": "Hi", "voice": "bf_emma"}).status_code == 200
    assert fake_engine.calls == [("Hi", "bf_emma", 1.0)]
    assert client.post("/v1/audio/speech", json={"input": "Default"}).status_code == 200
    assert fake_engine.calls[-1] == ("Default", "af_bella", 1.0)


@pytest.mark.parametrize("payload,status", [
    ({}, 422), ({"input": 4}, 422), ({"input": ""}, 400),
    ({"input": "  "}, 400), ({"input": "!!!"}, 400),
    ({"input": "x" * 5001}, 400), ({"input": "Hello", "voice": "unknown"}, 400),
    ({"input": "Hello", "speed": 3}, 422), ({"input": "Hi", "speed": 0.2}, 422),
    ({"input": "Hello", "response_format": "flac"}, 422),
    ({"input": "Hello", "voice": None}, 422),
])
def test_validation(client, payload, status):
    result = client.post("/v1/audio/speech", json=payload)
    assert result.status_code == status
    assert "error" in result.json()


@pytest.mark.parametrize("path,payload", [
    ("/v1/audio/speech", {"input": "Hello"}),
    ("/speak/stream", {"text": "Hello"}),
])
def test_new_routes_keep_security_guards(client, path, payload):
    assert client.post(path, json=payload, headers={"Host": "evil.example"}).status_code == 400
    assert client.post(path, json=payload, headers={"Origin": "https://evil.example"}).status_code == 403
    assert client.post(path, content=b"x" * 65537).status_code == 413


def test_optional_encoder_missing(client, monkeypatch, fake_engine):
    monkeypatch.setattr("tts.audio.shutil.which", lambda name: None)
    for fmt in ("mp3", "opus"):
        response = client.post("/v1/audio/speech", json={"input": "Hi", "response_format": fmt})
        assert response.status_code == 503
        assert "FFmpeg" in response.json()["error"]
    assert fake_engine.calls == []
    assert client.post("/v1/audio/speech", json={"input": "Hi"}).status_code == 200


@pytest.mark.parametrize("fmt,media", [("mp3", "audio/mpeg"), ("opus", "audio/ogg")])
@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="optional system FFmpeg not installed")
def test_encoded_formats_decode(client, fmt, media):
    response = client.post("/v1/audio/speech", json={"input": "Hi", "response_format": fmt})
    assert response.status_code == 200
    assert response.headers["content-type"] == media
    decoded = subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", "pipe:0", "-f", "s16le", "pipe:1",
    ], input=response.content, capture_output=True, check=True)
    assert len(decoded.stdout) > 0


def test_encoder_failure_is_sanitized(monkeypatch):
    monkeypatch.setattr("tts.audio.shutil.which", lambda name: "/usr/bin/ffmpeg")
    def fail(*args, **kwargs):
        raise subprocess.TimeoutExpired("ffmpeg", 60, stderr="private detail")
    monkeypatch.setattr("tts.audio.subprocess.run", fail)
    with pytest.raises(EncoderError, match="encoding failed") as exc:
        encode_audio(np.zeros(240), 24000, "mp3")
    assert "private detail" not in str(exc.value)


def parse_events(response):
    return [(block.splitlines()[0].removeprefix("event: "),
             json.loads(block.splitlines()[1].removeprefix("data: ")))
            for block in response.text.strip().split("\n\n")]


def test_sentence_stream(client, fake_engine):
    response = client.post("/speak/stream", json={"text": "One. Two! Three?", "speed": 1.2})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_events(response)
    assert [name for name, data in events] == ["audio", "audio", "audio", "done"]
    for index, (_, data) in enumerate(events[:-1]):
        assert data["index"] == index and data["content_type"] == "audio/wav"
        _, rate = sf.read(io.BytesIO(base64.b64decode(data["audio"])))
        assert rate == 24000
    assert fake_engine.calls == [(text, "af_bella", 1.2) for text in ["One.", "Two!", "Three?"]]


def test_stream_initial_error_is_http_error(make_client):
    client = make_client(FakeEngine(fail_with=RuntimeError("private detail")))
    response = client.post("/speak/stream", json={"text": "Hello. Again."})
    assert response.status_code == 500
    assert "private detail" not in response.text


def test_stream_later_error_is_event(make_client):
    class LaterFailure(FakeEngine):
        def synthesize(self, *args, **kwargs):
            if self.calls:
                raise RuntimeError("private detail")
            return super().synthesize(*args, **kwargs)
    engine = LaterFailure()
    app = create_app(Settings(), engine)
    from fastapi.testclient import TestClient
    with TestClient(app, base_url="http://localhost") as client:
        response = client.post("/speak/stream", json={"text": "One. Two."})
    assert [name for name, _ in parse_events(response)] == ["audio", "error"]
    assert "private detail" not in response.text
    assert app.state.pending == 0


def test_sentence_split():
    assert split_sentences(" One. Two!\nThree? Tail ") == ["One.", "Two!", "Three?", "Tail"]
    assert split_sentences("No punctuation") == ["No punctuation"]


def test_stream_first_clip_precedes_later_synthesis_and_close_releases_slot():
    import asyncio

    from server import SpeakRequest
    engine = FakeEngine()
    app = create_app(Settings(max_queue=1), engine)
    endpoint = next(route.endpoint for route in app.routes if route.path == "/speak/stream")

    async def scenario():
        response = await endpoint(SpeakRequest(text="First. Second."))
        assert app.state.pending == 1
        first = await anext(response.body_iterator)
        assert first.startswith("event: audio")
        assert [call[0] for call in engine.calls] == ["First."]
        await response.body_iterator.aclose()
        assert app.state.pending == 0

    asyncio.run(scenario())


def test_new_routes_share_admission_limit():
    import asyncio

    from fastapi import HTTPException

    from server import AudioSpeechRequest, SpeakRequest
    engine = FakeEngine()
    app = create_app(Settings(max_queue=1), engine)
    endpoints = {route.path: route.endpoint for route in app.routes if hasattr(route, "endpoint")}

    async def scenario():
        stream = await endpoints["/speak/stream"](SpeakRequest(text="First. Second."))
        for path, req in [
            ("/speak", SpeakRequest(text="Busy")),
            ("/v1/audio/speech", AudioSpeechRequest(input="Busy")),
            ("/speak/stream", SpeakRequest(text="Busy")),
        ]:
            with pytest.raises(HTTPException) as exc:
                await endpoints[path](req)
            assert exc.value.status_code == 503
        await anext(stream.body_iterator)
        await stream.body_iterator.aclose()
        assert app.state.pending == 0

    asyncio.run(scenario())
