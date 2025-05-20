# Create a directory for the SSL certificates (optional)
mkdir ~/ssl-certs
cd ~/ssl-certs

# Generate the private key
openssl genrsa -out server.key 2048

# Generate the certificate signing request (CSR)
openssl req -new -key server.key -out server.csr

# Generate a self-signed certificate
openssl x509 -req -in server.csr -signkey server.key -out server.crt
