FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN python build_excellence_v10.py
ENV HOST=0.0.0.0 PORT=8080 SHORELINE_DB=/data/shoreline.sqlite3
RUN mkdir -p /data
EXPOSE 8080
CMD ["python", "intelligence.py"]
