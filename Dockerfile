# Dockerfile (reference)
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# bring the app + Reports.json
COPY . .

# Streamlit on Cloud Run must listen on 0.0.0.0:8080
ENV PORT=8080
EXPOSE 8080
CMD ["streamlit","run","streamlit_app.py","--server.port=8080","--server.address=0.0.0.0","--server.headless=true"]

