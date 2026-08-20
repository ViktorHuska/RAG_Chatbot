# Image for the public demo (Hugging Face Spaces, Docker SDK). Same image runs
# on Fly.io, Render, or a VPS — only the port number is Spaces-specific.

FROM python:3.13-slim

# Spaces run the container as uid 1000. Build as that user too, so everything
# written at build time — the Chroma index, the employee DB, the embedding
# model cache — is owned by the same user that writes chats.db at runtime.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

WORKDIR /home/user/app

# Dependencies first, on their own layer: editing code does not reinstall them.
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=user . .

# Bake the index into the image. This downloads the embedding model (~420 MB)
# and embeds the corpus at build time, so a container start is seconds and the
# running app never needs network access to anything but the Anthropic API.
RUN python -m scripts.build_index

EXPOSE 7860

# The port is read from the environment because hosts disagree about it: Cloud
# Run and Render inject $PORT, Hugging Face Spaces expect 7860. The default
# keeps `docker run -p 7860:7860` working with no arguments.
#
# Shell form, so ${PORT} is actually expanded — the exec form would pass the
# literal string to uvicorn. `exec` then replaces the shell with uvicorn, so
# the server is PID 1 and receives SIGTERM directly; without it the shell would
# swallow the signal and the platform would wait out its grace period on every
# deploy.
CMD ["sh", "-c", "exec uvicorn app.server:app --host 0.0.0.0 --port ${PORT:-7860}"]