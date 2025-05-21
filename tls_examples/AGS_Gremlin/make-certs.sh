set -euo pipefail
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]
then
  export MSYS_NO_PATHCONV=1
fi

CA_CN="${1:-exampleCluster}"

SEC_DIR="security"
mkdir -p "$SEC_DIR"

GTLS_DIR="g-tls"
mkdir -p "$GTLS_DIR"

INTR_DIR="intermediate"
mkdir -p "$INTR_DIR"

CA_KEY="$SEC_DIR/ca.key"
CA_CERT="$SEC_DIR/ca.crt"
SERVER_CSR="$INTR_DIR/ca.crl"
SERVER_KEY="$GTLS_DIR/server.key"
SERVER_CSR="$INTR_DIR/server.csr"
SERVER_CERT="$GTLS_DIR/server.crt"

echo "checking openssl..."
if ! command -v openssl
then
    echo "openssl could not be found"
    exit 1
fi
openssl_version=$(openssl version)
echo "found ${openssl_version}"

echo "→ Generating CA key → $CA_KEY"
openssl genpkey -algorithm RSA -out "$CA_KEY" -pkeyopt rsa_keygen_bits:2048

echo "→ Generating self-signed CA cert → $CA_CERT"
openssl req -x509 -new -nodes -key "$CA_KEY" \
  -subj  "/CN=${CA_CN}" -days 365 \
  -out "$CA_CERT" \
  -addext "basicConstraints = critical,CA:TRUE,pathlen:0" \
  -addext "keyUsage = critical,keyCertSign,cRLSign" \

echo "→ Generating server key → $SERVER_KEY"
openssl genpkey -algorithm RSA -out "$SERVER_KEY" -pkeyopt rsa_keygen_bits:2048

echo "Signing server CSR with CA"
openssl req -new -key "$SERVER_KEY" \
  -subj "/C=US/ST=California/L=San Francisco/O=ExampleCorp/OU=DevOps/CN=${CA_CN}" \
  -out "$SERVER_CSR" \


echo "Signing server CERT with CA"
openssl x509 -req -in "$SERVER_CSR" -CA "$CA_CERT"  -CAkey "$CA_KEY" \
 -out "$SERVER_CERT" -days 365 -subj  "/CN=${CA_CN}" \

echo "removing intermediate files"
rm -r "$INTR_DIR"

  echo "Files generated:"
  echo "  ca.key    — your CA private key"
  echo "  ca.crt    — your CA certificate"
  echo "  server.key— your server private key"
  echo "  server.crt— your server certificate"