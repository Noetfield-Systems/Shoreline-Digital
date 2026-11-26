FROM python:3.12-slim
WORKDIR /app
COPY . .
ENV HOST=0.0.0.0 PORT=8080 SHORELINE_DB=/data/shoreline.sqlite3
RUN mkdir -p /data
EXPOSE 8080
CMD ["python", "growth.py"]
