FROM python:3.13-slim
WORKDIR /app
COPY server.py /app/server.py
ENV PYTHONUNBUFFERED=1 ANALYTICS_DATA_DIR=/data
CMD ["python", "/app/server.py"]
