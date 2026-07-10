# Secure Speech-to-Text - GPU Dockerfile (CUDA 12.8 + cuDNN)
FROM nvidia/cuda:12.8.0-cudnn-runtime-ubuntu22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Fix PyTorch 2.6+ weights_only default change (pyannote models need this)
ENV TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1

# Install Python 3.13 and system dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.13 \
    python3.13-venv \
    python3.13-dev \
    python3-pip \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.13 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.13 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1

# Bootstrap pip for Python 3.13 (distutils removed in 3.12+)
RUN python -m ensurepip --upgrade \
    && python -m pip install --upgrade pip

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies (whisperx handles PyTorch)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure cuDNN from pip is on the library path (needed for torch 2.8 + cuDNN 9.x)
ENV LD_LIBRARY_PATH=/usr/local/lib/python3.13/dist-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH

# Copy application code
COPY . .

# Create input/output directories
RUN mkdir -p input output

# Set default command
ENTRYPOINT ["python", "secure_speech_to_text.py"]
CMD ["--help"]

