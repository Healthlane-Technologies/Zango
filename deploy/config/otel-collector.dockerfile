FROM nixos/nix

RUN nix-env -iA nixpkgs.opentelemetry-collector

COPY config/collector.yml /etc/otel-collector-config.yaml
COPY --chmod=755 start_otel.sh /start_otel.sh
