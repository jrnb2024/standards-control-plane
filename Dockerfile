FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip \
    && pip install -e .

EXPOSE 3787

CMD ["standards-control-plane", "serve", "--host", "0.0.0.0", "--port", "3787"]
