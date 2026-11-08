# Hook it to your LLM

Your LLM generates text; VoiceForge speaks it. The speech base URL is
`http://127.0.0.1:8000/v1`, **not** a chat-completions backend.

## One copy-paste speech hookup

With VoiceForge already set up and running, send text straight to the speech API:

```bash
curl --fail-with-body http://127.0.0.1:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"voiceforge","input":"Hello from your local LLM.","voice":"nova","response_format":"wav","speed":1.0}' \
  --output hello.wav
```

Your client base URL is `http://127.0.0.1:8000/v1`; replace `input` with the LLM's
answer. The setups below automate that handoff or configure Open WebUI's TTS.

## Check speech first

Start your installed VoiceForge with `voiceforge serve`. Defaults are
`VOICEFORGE_HOST=127.0.0.1` and `VOICEFORGE_PORT=8000`. These examples assume the
Kokoro files are already installed; no model download commands are included.
`GET /health` must show `model_loaded: true`: HTTP 200 alone can mean degraded.

```bash
curl --fail-with-body http://127.0.0.1:8000/health
curl --fail-with-body http://127.0.0.1:8000/voices
curl --fail-with-body http://127.0.0.1:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"voiceforge","input":"Hello from VoiceForge.","voice":"nova","response_format":"wav","speed":1.0}' \
  --output hello.wav
```

Play `hello.wav` in your normal audio player. The snippets below use Bash, curl
and jq; they save audio rather than automatically play it.

| Field | Default | Contract |
| --- | --- | --- |
| `input` | required | Trimmed text, 1–5,000 characters; must contain letters or numbers. Split longer replies yourself. |
| `model` | `voiceforge` | Compatibility label; does not switch/download models. |
| `voice` | `af_bella` | Native English voice ID from `/voices`, or an alias below. |
| `response_format` | `wav` | Only `wav`, `mp3`, `opus`. MP3/Opus require system FFmpeg; missing encoder returns 503. WAV needs no FFmpeg. |
| `speed` | `1.0` | Finite number, 0.5–2.0. |

Aliases: `alloy` → `af_heart`, `echo` → `am_adam`, `fable` → `bm_george`,
`onyx` → `am_michael`, `nova` → `af_bella`, `shimmer` → `af_sarah`.

VoiceForge has **no authentication**. If a non-browser client requires a key,
`not-needed` is a dummy value, not protection. Keep loopback defaults; host,
origin and body-size guards still apply. `/v1/audio/speech` returns audio bytes;
`/speak/stream` is a separate sentence-event protocol, not this endpoint.

## Ollama → VoiceForge

With Ollama running on its usual port 11434, choose an **already-installed**
model (`ollama list`). The documented `/api/generate` with `stream:false`
returns the text in `response`:

```bash
export OLLAMA_MODEL='your-installed-model'
set -o pipefail
curl --fail-with-body http://127.0.0.1:11434/api/generate \
  -H 'Content-Type: application/json' \
  -d "$(jq -n --arg model "$OLLAMA_MODEL" \
       '{model:$model,prompt:"Say hello in one short sentence.",stream:false}')" |
  jq -e '{model:"voiceforge",input:.response,voice:"nova",response_format:"wav",speed:1.0}
         | select((.input | type) == "string" and (.input | length) > 0)' |
  curl --fail-with-body http://127.0.0.1:8000/v1/audio/speech \
    -H 'Content-Type: application/json' --data-binary @- --output ollama.wav
```

This bridges two HTTP calls; there is no Ollama TTS setting to configure here.

## llama.cpp → VoiceForge

With an installed binary and existing chat-capable GGUF, start your LLM server
in another terminal (8080 avoids VoiceForge's 8000):

```bash
llama-server -m /absolute/path/to/your-existing-model.gguf \
  --host 127.0.0.1 --port 8080 --alias local
```

Then forward only `choices[0].message.content` from its documented chat endpoint:

```bash
set -o pipefail
curl --fail-with-body http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"local","messages":[{"role":"user","content":"Say hello in one short sentence."}],"stream":false}' |
  jq -e '{model:"voiceforge",input:.choices[0].message.content,voice:"nova",response_format:"wav",speed:1.0}
         | select((.input | type) == "string" and (.input | length) > 0)' |
  curl --fail-with-body http://127.0.0.1:8000/v1/audio/speech \
    -H 'Content-Type: application/json' --data-binary @- --output llamacpp.wav
```

This is an HTTP bridge, not a built-in VoiceForge setting. Chat behavior depends
on the model and its supported chat template.

## Open WebUI: TTS only

For an already-installed **native** Open WebUI process in the same host/network
namespace as VoiceForge, export these documented TTS environment variables in
its launch environment, then start/restart it with your existing launch command:

```bash
export AUDIO_TTS_ENGINE=openai
export AUDIO_TTS_OPENAI_API_BASE_URL=http://127.0.0.1:8000/v1
export AUDIO_TTS_OPENAI_API_KEY=not-needed
export AUDIO_TTS_MODEL=voiceforge
export AUDIO_TTS_VOICE=nova
```

Keep the chat connection pointed at Ollama or llama.cpp. These TTS-specific
variables are not the chat `OPENAI_API_BASE_URL`. This guide uses documented
environment variables rather than a version-dependent sidebar click-path.
Existing saved audio settings may need updating in your deployment.

Clients that request MP3 require FFmpeg on the VoiceForge host. If playback
fails, first try the explicit WAV curl above and inspect `/health` and HTTP errors.

**Docker:** loopback inside a container is that container, not your host. The
URL above is not a drop-in recipe for an isolated container. Follow the official
networking documentation for your deployment; reaching a host service may also
require intentional VoiceForge bind/allowed-host changes. Do not expose this
unauthenticated server publicly to solve networking.

## Sources and scope

Examples match [`AudioSpeechRequest`/`VOICE_ALIASES`](../server.py) and the
[fake-engine API tests](../tests/test_voiceforge_openai.py). They are checked
against the contract, not an end-to-end test of every LLM/client version.

- [Ollama generate API](https://docs.ollama.com/api/generate): `/api/generate`, `model`, `prompt`, `stream`, `response`.
- [llama.cpp server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md): `--host`, `--port`, `--alias`, `/v1/chat/completions` and message content.
- [Open WebUI audio reference](https://docs.openwebui.com/troubleshooting/audio.md): TTS variables and Docker loopback caveat.
- [Open WebUI compatible providers](https://docs.openwebui.com/getting-started/quick-start/connect-a-provider/starting-with-openai-compatible.md): separate TTS base URL and `/v1/audio/speech`.
