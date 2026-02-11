FROM python:3.10-slim

WORKDIR /app

RUN apt-get update -y && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends ffmpeg curl unzip ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Deno install (stabil link)
RUN curl -fsSL https://deno.land/x/install/install.sh | sh

ENV DENO_INSTALL="/root/.deno"
ENV PATH="${DENO_INSTALL}/bin:${PATH}"

COPY requirements.txt .
RUN pip install -U pip && pip install -U -r requirements.txt

COPY . .

CMD ["bash", "start"]
