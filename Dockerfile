<<<<<<< HEAD

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app
ENV PYTHONPATH=/app

RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY tests/ ./tests/
COPY wsgi.py ./

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2)" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "30", "wsgi:app"]
=======
# Use a lean, minimal base image statement
   FROM node:18-alpine

   # Set the internal execution directory 
   WORKDIR /app

   # Copy application source files from your laptop into the container
   COPY . .

   # Define the main executable script in strict JSON Exec format
   CMD ["echo", "DecodeLabs Container Mastered Successfully!"]
>>>>>>> d49a400ee455777fb9f3687268c885bb6c29c586
