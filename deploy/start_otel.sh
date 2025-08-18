#!/bin/sh
if [ "$OTEL_IS_ENABLED" = "true" ]; then
    exec otelcol --config=/etc/otel-collector-config.yaml
else
    exit 0
fi
