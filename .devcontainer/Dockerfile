FROM ubuntu:latest

RUN mkdir /workspace
WORKDIR /workspace
COPY . .

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    make \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_LINK_MODE=copy
RUN echo 'eval "$(uv generate-shell-completion bash)"' >> ~/.bashrc && \
    uv sync && uv run pre-commit install \
    && echo 'source /workspace/.venv/bin/activate' >> ~/.bashrc
