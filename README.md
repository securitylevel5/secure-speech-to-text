# Secure Speech-to-Text

A local, privacy-first toolkit for transcribing sensitive meetings and generating executive summaries, all without sending data to the cloud.

---

## Overview

Security professionals often need to transcribe sensitive meetings (strategy discussions, incident reviews, classified briefings) and generate executive summaries. Cloud-based transcription services pose unacceptable risks for this content.

**Secure Speech-to-Text** provides an easy, fully local way to transcribe audio and generate executive summaries, keeping sensitive information off third-party servers. All processing happens on your machine using open-source models and local LLMs.

---

## Features

- **End-to-End Workflow:** Interactive script guides you through transcription, summary, and secure deletion
- **Docker Support:** Single-command transcription with GPU or CPU containers
- **Local Processing:** All transcription runs on your machine; no data leaves your network
- **Executive Summaries:** Generate summaries via any OpenAI-compatible API (LM Studio, Ollama, vLLM)
- **Speaker Diarization:** Identify and label different speakers in conversations
- **Word-Level Timestamps:** Accurate timing for each word using alignment models
- **Multiple Output Formats:** SRT, VTT, TXT, JSON
- **GPU Acceleration:** CUDA support for fast inference (CPU fallback available)
- **Best-Effort Secure Deletion:** Overwrite and remove source audio after transcription

---

## Quick Start with Docker

The easiest way to run Secure Speech-to-Text is with Docker.

### 1. Configure Environment

Copy `.env.example` to `.env` and add your Hugging Face token (required for speaker diarization):

```bash
cp .env.example .env
# Edit .env and set HUGGINGFACE_HUB_TOKEN=your_token_here
```

### 2. Build and Run

**GPU (NVIDIA CUDA):**

```bash
# Build the GPU image
docker compose build gpu

# Place your audio file in the input/ folder, then run:
docker compose run --rm gpu input/meeting.m4a -y
```

**CPU Only:**

```bash
# Build the CPU image
docker compose build cpu

# Place your audio file in the input/ folder, then run:
docker compose run --rm cpu input/meeting.m4a -y
```

Results appear in the `output/` folder.

---

## Usage

### Command-Line Options

```bash
python secure_speech_to_text.py [OPTIONS] <audio_file>
```

| Flag | Description |
|------|-------------|
| `-y`, `--no-interactive` | Skip prompts, run full pipeline |
| `--no-summary` | Skip executive summary generation |
| `--no-delete` | Skip secure deletion of source audio |
| `--no-diarize` | Disable speaker diarization |
| `--output-dir PATH` | Override output directory (default: `output/`) |

### Examples

```bash
# Interactive mode (prompts at each step)
python secure_speech_to_text.py input/meeting.m4a

# Non-interactive mode (runs full pipeline)
python secure_speech_to_text.py input/meeting.m4a -y

# Skip summary generation
python secure_speech_to_text.py input/meeting.m4a -y --no-summary

# Custom output directory
python secure_speech_to_text.py meeting.m4a --output-dir ./my-transcripts
```

### Input/Output Folders

- Place audio files in `input/`
- Results appear in `output/<filename>_<timestamp>/`:
  - `*.txt`: Plain text transcript
  - `*.srt`, `*.vtt`: Subtitle formats
  - `*.json`: Detailed word-level data
  - `executive_summary.md`: LLM-generated summary

---

## Local Installation

### Prerequisites

- **Python 3.9 to 3.13** (3.14+ not supported by WhisperX)
- FFmpeg installed and on PATH
- A local LLM server for executive summaries (optional)

```bash
# Windows (Chocolatey)
choco install ffmpeg

# macOS (Homebrew)
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install -y ffmpeg
```

### Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

2. **(GPU only)** Install CUDA Toolkit 12.8 before WhisperX. Skip this step if using CPU only.
   - **Linux:** Follow the [CUDA Installation Guide for Linux](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/)
   - **Windows:** Download and install from [CUDA Downloads](https://developer.nvidia.com/cuda-downloads)

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure your LLM API (copy `.env.example` to `.env` and edit):

```bash
cp .env.example .env
```

---

## Configuration

### LLM API Setup

Create a `.env` file (or copy from `.env.example`):

```bash
# OpenAI-compatible API endpoint
API_BASE_URL=http://localhost:1234/v1

# API key (use any value for local servers)
API_KEY=lm-studio

# Model name as shown in your LLM server
MODEL_NAME=local-model
```

**Supported servers:**
- [LM Studio](https://lmstudio.ai/): `http://localhost:1234/v1`
- [Ollama](https://ollama.ai/): `http://localhost:11434/v1`
- [vLLM](https://github.com/vllm-project/vllm): `http://localhost:8000/v1`

### Hugging Face Access (Required for Diarization)

WhisperX uses pyannote for speaker diarization. To enable diarization:

1. Create a Hugging Face account and generate a User Access Token with "Read" permissions at [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

2. Accept the model conditions for both:
   - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
   - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)

3. Provide your token via one of these methods:

**Option A: Add to `.env` file (recommended for Docker):**

```bash
HUGGINGFACE_HUB_TOKEN=your_token_here
```

**Option B: Login via CLI (for local installation):**

```bash
huggingface-cli login
```

**Option C: Set environment variable:**

```powershell
# Windows PowerShell
setx HUGGINGFACE_HUB_TOKEN "<YOUR_TOKEN>"
$env:HUGGINGFACE_HUB_TOKEN = "<YOUR_TOKEN>"  # for current session
```

```bash
# macOS/Linux
export HUGGINGFACE_HUB_TOKEN="<YOUR_TOKEN>"
```

---

## Utilities

### Token Counter

Determine token count of transcript files for sizing your LLM's context window:

```bash
python -m utils.token_counter transcript.txt
```

Options:
- `--method`: Choose tokenizer (`tiktoken` or `transformers`, default: `tiktoken`)
- `--model`: Specify model name (default: `gpt-4` for tiktoken, `gpt2` for transformers)

```bash
# Use transformers library with specific model
python -m utils.token_counter transcript.txt --method transformers --model mistralai/Mistral-7B-v0.1
```

---

## Project Structure

```
sl5-speech-to-text/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── .env.example              # API configuration template
├── secure_speech_to_text.py         # Main workflow script
├── best_effort_delete.py     # Secure deletion helper
├── Dockerfile                # GPU container (CUDA 12.8)
├── Dockerfile.cpu            # CPU container
├── docker-compose.yml        # Docker services
├── input/                    # Place audio files here
├── output/                   # Transcripts and summaries appear here
└── utils/
    └── token_counter.py      # Token counting for LLM context sizing
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "ffmpeg not found" | Ensure ffmpeg is installed and on PATH (see Prerequisites) |
| GPU not used | Check your PyTorch install matches your CUDA version |
| Module not found | Run `pip install -r requirements.txt` inside your venv |
| Diarization fails | Ensure you've accepted model conditions on Hugging Face |
| LLM summary fails | Check your `.env` configuration and that your LLM server is running |
| Docker GPU error | Ensure NVIDIA Container Toolkit is installed |
| `WeightsUnpickler error` | Set env var: `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1` (PyTorch 2.6+ issue) |

---

## TODO

- **Speaker Identification:** Ability to label which speaker is whom (e.g., "SPEAKER_00 is John")

---

## Dependencies

| Component | Dependency |
|-----------|------------|
| **Transcription** | WhisperX, PyTorch, FFmpeg |
| **Diarization** | pyannote (via Hugging Face) |
| **Executive Summary** | openai, python-dotenv |
| **Token Counting** | tiktoken, transformers (optional) |
| **Docker GPU** | NVIDIA Container Toolkit |

---

## License

Created by **[Security Level 5](https://sl5.org)** for the security community.
Licensed under the [MIT License](LICENSE).

---

## Related Resources

- [WhisperX](https://github.com/m-bain/whisperX): Fast Whisper with word-level timestamps
- [OpenAI Whisper](https://github.com/openai/whisper): Original Whisper model
- [pyannote](https://github.com/pyannote/pyannote-audio): Speaker diarization toolkit
- [LM Studio](https://lmstudio.ai/): Run local LLMs with a GUI
- [Ollama](https://ollama.ai/): Run local LLMs from the command line
- [vLLM](https://github.com/vllm-project/vllm): High-throughput LLM inference
- [PyTorch](https://pytorch.org/get-started/locally/): GPU-accelerated deep learning
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html): Docker GPU support
