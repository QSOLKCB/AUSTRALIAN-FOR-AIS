# AudioPod integration boundary

AudioPod v0.1.0 (QSOLKCB/AudioPod) is a local EPUB/TXT/Markdown-to-speech
application using Piper ONNX. It is NOT a speech recognizer or translator.

Potential future cross-project bridge:

1. Pass separately authored text through AudioPod for pronunciation/prosody
   experiments. Record voice ONNX and configuration digests, speed, rendering
   style and PCM sample measurements.
2. Keep all synthesized audio in a **synthetic** labelled split; synthetic
   speech cannot establish Australian accent robustness on natural speakers.
3. Add a separate offline ASR adapter (not an AudioPod dependency) and test
   Aussie audio transcription accuracy with speaker-disjoint held-out data.
4. Only after ASR, consider a distinct, auditable semantic-normalization stage
   that preserves meaning, profanity and context without homogenizing dialect.
5. Report speech WER/CER, task meaning retention and synthesized voice
   naturalness as different metrics. Use actual listening review where relevant.

No AudioPod source was changed by this Toolkit prototype.
