FROM ghcr.io/meta-pytorch/openenv-base:latest

WORKDIR /app/env

COPY . /app/env

RUN pip install -e . --no-cache-dir

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

CMD ["python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
