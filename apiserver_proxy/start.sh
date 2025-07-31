#!/bin/bash

function refresh_header {
    echo -n 'proxy_set_header X-Serverless-Authorization "Bearer ' > /tmp/id_header.conf
    curl -H "Metadata-Flavor: Google" \
    'http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience=https://apiserver-411490623960.us-central1.run.app' >> /tmp/id_header.conf
    echo '";' >> /tmp/id_header.conf
}

refresh_header
nginx -g "daemon off;"
while true; do
    sleep 600
    refresh_header
    nginx -s reload
done
