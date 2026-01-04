#!/bin/sh
set -e

# Generate datasource config from environment variables if template exists
if [ -f /etc/grafana/provisioning/datasources/datasource.yml.template ]; then
  sed -e "s|\$POSTGRES_USER|${POSTGRES_USER}|g" \
      -e "s|\$POSTGRES_PASSWORD|${POSTGRES_PASSWORD}|g" \
      -e "s|\$POSTGRES_DB|${POSTGRES_DB}|g" \
      /etc/grafana/provisioning/datasources/datasource.yml.template > /etc/grafana/provisioning/datasources/datasource.yml
fi

# Run the original Grafana entrypoint
exec /run.sh "$@"

