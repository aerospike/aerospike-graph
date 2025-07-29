#!/bin/bash
set -euo pipefail
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]
then
  export MSYS_NO_PATHCONV=1
fi

CA_CN="${1:-exampleCluster}" # Cluster name to sign certs with

SEC_DIR="security"
mkdir -p "$SEC_DIR"

CA_KEY="$SEC_DIR/ca.key"
CA_CERT="$SEC_DIR/ca.crt"
SERVER_KEY="$SEC_DIR/server.key"
SERVER_CSR="$SEC_DIR/server.csr"
SERVER_CERT="$SEC_DIR/server.crt"

echo "Checking system for openssl command."
if ! command -v openssl
then
    echo "openssl command not found. Please install openssl before running this script."
    exit 1
fi
openssl_version=$(openssl version)
echo "Found ${openssl_version}."


echo "Generating CA key '$CA_KEY'."
openssl genpkey -algorithm RSA -out "$CA_KEY" -pkeyopt rsa_keygen_bits:2048

echo "Generating self-signed CA cert '$CA_CERT'."
openssl req -x509 -new -nodes -key "$CA_KEY" \
  -subj  "/CN=${CA_CN}" -days 365 \
  -out "$CA_CERT"

echo "Generating server key '$SERVER_KEY'."
# Server private key
openssl genpkey -algorithm RSA -out "$SERVER_KEY" -pkeyopt rsa_keygen_bits:2048

echo "Signing server CSR with CA."
openssl req -new -key "$SERVER_KEY" \
  -subj "/C=US/ST=California/L=San Francisco/O=ExampleCorp/OU=DevOps/CN=${CA_CN}" \
  -out "$SERVER_CSR"

echo "Signing server CERT with CA."
# Sign it with your CA
openssl x509 -req -in "$SERVER_CSR" -CA "$CA_CERT"  -CAkey "$CA_KEY" \
   -out "$SERVER_CERT" -days 365 -CAcreateserial

echo "Removing intermediate files."
rm -f "$SEC_DIR/ca.srl" \
      "$SEC_DIR/server.csr"

echo "Files generated:"
echo "  ca.key     — your CA private key"
echo "  ca.crt     — your CA certificate"
echo "  server.key — your server private key"
echo "  server.crt — your server certificate"
