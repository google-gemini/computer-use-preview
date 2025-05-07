FROM marketplace.gcr.io/google/ubuntu2404:latest

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -yq --no-install-recommends python3 python3-pip

ENV PYTHONUNBUFFERED=True
ENV APP_HOME=/app

WORKDIR $APP_HOME
COPY . ./

RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

ENV PORT=8080
ENV FORWARDED_ALLOW_IPS=*
EXPOSE 8080
ENTRYPOINT ["sh", "-c", "uvicorn app:app --host=0.0.0.0 --port=${PORT}"]