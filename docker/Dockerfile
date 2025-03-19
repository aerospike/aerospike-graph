ARG VERSION
FROM aerospike/aerospike-graph-service:${VERSION} AS build

ARG BULKLOADER

# Set environment variables.
ENV CONF_DIR="/opt/conf"

COPY ${BULKLOADER} /opt/bulk-loader.jar

WORKDIR /opt

FROM aerospike/aerospike-graph-service:${VERSION} AS main

COPY --from=build /opt /opt

WORKDIR /opt

HEALTHCHECK CMD ls $HEALTHCHECK_FILE

ENTRYPOINT ["scripts/gremlin-server-docker.sh"]
