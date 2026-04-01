import datetime
import ipaddress
import os

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def generate_cert(domain="keycloak.localhost", cert_dir="certs"):
    os.makedirs(cert_dir, exist_ok=True)
    cert_path = os.path.join(cert_dir, "tls.crt")
    key_path = os.path.join(cert_dir, "tls.key")

    if os.path.exists(cert_path) and os.path.exists(key_path):
        print(f"[skip] Certs already exist in '{cert_dir}/'.")
        return os.path.abspath(cert_path), os.path.abspath(key_path)

    print(f"[tls] Generating cert for '{domain}'...")

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    name = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, domain),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Local Dev"),
    ])

    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(domain),
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ))

    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"[ok] Cert -> {cert_path}")
    print(f"[ok] Key  -> {key_path}")
    return os.path.abspath(cert_path), os.path.abspath(key_path)
