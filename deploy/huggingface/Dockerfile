# Bauanleitung für Hugging Face Spaces (Docker).
# ACHTUNG: Seit Juli 2026 brauchen Docker-Spaces bei Hugging Face ein kostenpflichtiges PRO-Abo.
# Kostenlose Alternative: GitHub Codespaces, siehe docs/IPHONE-HOSTING.md
# Diese Datei wird 1:1 als "Dockerfile" in deinen Space kopiert.
# Sie lädt die App direkt aus dem öffentlichen GitHub-Repository – du musst keine Dateien hochladen.
FROM python:3.12-slim

# Fette Schrift für die Untertitel (FFmpeg bringt die App selbst mit)
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core && rm -rf /var/lib/apt/lists/*

# Hugging Face startet Container als Benutzer 1000
RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user

# Aktuellen Stand der App von GitHub holen (bei jedem Neustart mit "Factory rebuild" neu geladen)
ARG BRANCH=claude/tiktok-ai-video-generator-m6ldsj
ADD --chown=user https://github.com/tqm-cld/Tiktok-ai-generator/archive/refs/heads/${BRANCH}.tar.gz /tmp/app.tar.gz
RUN mkdir app && tar -xzf /tmp/app.tar.gz -C app --strip-components=1 && rm /tmp/app.tar.gz

WORKDIR /home/user/app
RUN pip install --no-cache-dir --user -r requirements.txt

ENV PATH=/home/user/.local/bin:$PATH \
    PORT=7860 \
    NO_BROWSER=1 \
    PYTHONUNBUFFERED=1
EXPOSE 7860
CMD ["python", "app.py"]
