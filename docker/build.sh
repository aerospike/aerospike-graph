#!/bin/bash

set -e

# ======================
# CONFIGURATION
# ======================
IMAGE_NAME="aerospike-graph-custom"
BULK_LOADER_URL_BASE="https://download.aerospike.com/artifacts/aerospike-graph-bulk-loader"

# ======================
# HELPERS
# ======================
usage() {
  echo "Usage: $0 <version>"
  exit 1
}

# ======================
# INPUT VALIDATION
# ======================
if [ $# -ne 1 ]; then
  usage
fi

VERSION="$1"

version_lt_or_eq() {
  [ "$(printf '%s\n' "$1" "$2" | sort -V | head -n1)" = "$1" ]
}

# Block versions <= 2.5.0, Aerospike Graph Service included the bulk loader automatically in non-slim builds of 2.5.0 and earlier.
MIN_SUPPORTED_VERSION="2.5.0"

if version_lt_or_eq "$VERSION" "$MIN_SUPPORTED_VERSION"; then
   echo "❌ Version $VERSION is not supported. Must be greater than $MIN_SUPPORTED_VERSION."
   exit 1
fi

# ======================
# DOWNLOAD JAR
# ======================
JAR_NAME="aerospike-graph-bulk-loader-${VERSION}.jar"
DOWNLOAD_URL="${BULK_LOADER_URL_BASE}/${VERSION}/${JAR_NAME}"

if [ -f "$JAR_NAME" ]; then
  echo "📦 Bulk loader JAR already exists: $JAR_NAME"
else
  echo "📦 Bulk loader JAR does not exist: $JAR_NAME"
  echo "🚀 Downloading bulk loader JAR from: $DOWNLOAD_URL"
  curl -fSL -o "$JAR_NAME" "$DOWNLOAD_URL"
fi

if [ ! -f "$JAR_NAME" ]; then
  echo "❌ Failed to download $DOWNLOAD_URL, verify this version exists before proceeding."
  exit 1
fi

echo "✅ Downloaded $DOWNLOAD_URL"

# ======================
# DOCKER BUILD
# ======================
echo "🔨 Building Docker image: ${IMAGE_NAME}:${VERSION}"

docker build \
  --build-arg VERSION="$VERSION" \
  --build-arg BULKLOADER="$JAR_NAME" \
  -t "${IMAGE_NAME}:${VERSION}" \
  -t "${IMAGE_NAME}:latest" \
  .

echo "✅ Docker image ${IMAGE_NAME}:${VERSION} built successfully!"
