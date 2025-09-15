# ---- Build a tiny image ----
FROM python:3.11-slim

# System deps (faster installs, clean layer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Copy requirements first (better Docker cache)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest
COPY . /app

# Streamlit in Cloud Run must bind to 0.0.0.0 and $PORT
ENV PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8080
CMD ["bash","-lc","streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port ${PORT:-8080}"]

