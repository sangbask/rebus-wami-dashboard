FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# install deps first (better cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy ALL app files: code + images + Reports.json/xlsx
COPY . .

ENV PORT=8080
EXPOSE 8080
CMD ["streamlit","run","streamlit_app.py","--server.port=8080","--server.address=0.0.0.0"]

