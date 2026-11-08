# Third-party notices

VoiceForge itself is licensed under the MIT License. See [LICENSE](LICENSE).

VoiceForge uses the following separate projects. Their licenses are not replaced
by VoiceForge’s MIT license.

## Kokoro-82M

- License: Apache License 2.0
- Project: https://huggingface.co/hexgrad/Kokoro-82M
- Full license text: [licenses/Apache-2.0.txt](licenses/Apache-2.0.txt)
- Official license: https://www.apache.org/licenses/LICENSE-2.0

The Kokoro model weights are Apache 2.0, not MIT. VoiceForge does not keep
those files in this repository. `download_models.py` fetches them from the
[kokoro-onnx `model-files-v1.0` release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0).
If you redistribute those model files with a product, include the Apache 2.0
license and any copyright or NOTICE text that accompanies the model.

## kokoro-onnx

- License: MIT License
- Copyright (c) 2025 github.com/thewh1teagle
- Project: https://github.com/thewh1teagle/kokoro-onnx
- Full license text: [licenses/kokoro-onnx-MIT.txt](licenses/kokoro-onnx-MIT.txt)

The MIT notice and permission text from that project are included in this
repository so they stay with VoiceForge.
