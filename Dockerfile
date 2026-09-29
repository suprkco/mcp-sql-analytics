FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home appuser
COPY analytics analytics
RUN python -m analytics.seed
USER appuser
CMD ["python", "-m", "analytics.demo"]
