# Lightweight Alpine Linux container (< 45 MB)
FROM python:3.11-alpine

WORKDIR /app

# Install minimal build tools for SQLite and math libraries
RUN apk add --no-cache gcc musl-dev linux-headers

COPY . /app

EXPOSE 8080

CMD ["python", "scripts/run_web.py", "8080"]
