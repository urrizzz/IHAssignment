FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl gnupg && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && apt-get install -y docker-ce-cli && \
    pip install --no-cache-dir groq pydantic python-dotenv && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["python", "main.py"]