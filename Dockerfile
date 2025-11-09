FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    flask==2.3.0 \
    flask-cors==4.0.0 \
    flask-socketio \
    pyyaml==6.0.1 \
    requests==2.31.0 \
    pytest==7.4.0 \
    pytest-cov==4.1.0

RUN mkdir -p logs results

EXPOSE 5000 6653

CMD ["python", "src/presentation/web/dashboard_app.py"]
