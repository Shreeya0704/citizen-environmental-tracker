FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/usr/local/lib/python3.11/site-packages:/usr/lib/python3/dist-packages

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY refresh.py /app/refresh.py
COPY refresh-loop.sh /app/refresh-loop.sh
RUN chmod +x /app/refresh-loop.sh

ENTRYPOINT ["/app/refresh-loop.sh"]
