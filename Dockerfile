FROM python:3.11.8-slim

WORKDIR /app

# Sistem paketleri
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl unzip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Deno (stabil)
RUN curl -fsSL https://deno.land/x/install/install.sh | sh

ENV DENO_INSTALL="/root/.deno"
ENV PATH="${DENO_INSTALL}/bin:/usr/local/bin:/usr/bin:/bin"

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir -r requirements.txt

# App
COPY . .

CMD ["bash", "start"]
