set -euo pipefail
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]
then
  export MSYS_NO_PATHCONV=1
fi

CA_CN="${1:-exampleCluster}" # Cluster name to sign certs with

SEC_DIR="security"
mkdir -p "$SEC_DIR"

GTLS_DIR="g-tls"
mkdir -p "$GTLS_DIR"

INTR_DIR="intermediate"
mkdir -p "$INTR_DIR"

CA_KEY="$SEC_DIR/ca.key"
CA_CERT="$SEC_DIR/ca.crt"
SERVER_KEY="$GTLS_DIR/server.key"
SERVER_CSR="$INTR_DIR/server.csr"
SERVER_CERT="$GTLS_DIR/server.crt"

echo "Checking system for openssl command."
if ! command -v openssl
then
    echo "openssl command not found. Please install openssl before running this script."
    exit 1
fi
openssl_version=$(openssl version)
echo "Found ${openssl_version}."

echo "Generating CA key '$CA_KEY'."

openssl genpkey -algorithm RSA \
  -out "$CA_KEY" -pkeyopt rsa_keygen_bits:2048

# Create the config for the CA
CA_CONFIG="$SEC_DIR/ca_openssl.cnf"
cat >"$CA_CONFIG"<<EOF
[ v3_ca ]
basicConstraints = critical,CA:TRUE
keyUsage = critical, digitalSignature, keyCertSign, cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
EOF

echo "Generating self-signed CA cert '$CA_CERT'."
openssl req -x509 -new -nodes \
  -key "$CA_KEY" \
  -days 365 \
  -out "$CA_CERT" \
  -subj "/CN=${CA_CN}" \
  -config "$CA_CONFIG" \
  -extensions v3_ca

echo "Generating server key '$SERVER_KEY'."
openssl genpkey -algorithm RSA -out "$SERVER_KEY" -pkeyopt rsa_keygen_bits:2048

echo "Signing server CSR with CA."
openssl req -new -key "$SERVER_KEY" \
  -subj "/C=US/ST=California/L=San Francisco/O=ExampleCorp/OU=DevOps/CN=${CA_CN}" \
  -out "$SERVER_CSR"

echo "Signing server CERT with CA."
openssl x509 -req -in "$SERVER_CSR" \
  -CA "$CA_CERT" -CAkey "$CA_KEY" -CAcreateserial \
  -out "$SERVER_CERT" -days 365 \
  -extfile "$CA_CONFIG"

echo "Removing intermediate files"
rm -rf "$INTR_DIR" "$SEC_DIR/ca.srl" "$CA_CONFIG"

echo "Files generated:"
echo "  $CA_KEY — your CA private key"
echo "  $CA_CERT — your CA certificate"
echo "  $SERVER_KEY — your server private key"
echo "  $SERVER_CERT — your server certificate"