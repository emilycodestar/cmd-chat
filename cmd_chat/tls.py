import ssl
import datetime
import ipaddress
import os
import tempfile
from typing import Optional

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_self_signed_cert(host: str) -> tuple[bytes, bytes]:
    """Generate a self-signed TLS certificate for the given host.

    Returns (cert_pem, key_pem) as bytes.
    """
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, host)])

    san: list[x509.GeneralName] = [x509.DNSName(host)]
    try:
        san.append(x509.IPAddress(ipaddress.ip_address(host)))
    except ValueError:
        pass

    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName(san), critical=False)
        .sign(key, hashes.SHA256())
    )

    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    return cert_pem, key_pem


def make_server_ssl_context(
    cert_path: Optional[str] = None,
    key_path: Optional[str] = None,
    host: str = "0.0.0.0",
) -> tuple[ssl.SSLContext, Optional[bytes]]:
    """Create a server-side SSLContext.

    If cert_path/key_path are not provided, a self-signed certificate is
    generated automatically.

    Returns (ssl_context, cert_pem) where cert_pem is the PEM bytes of the
    generated certificate (None when an existing cert/key pair is loaded).
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2

    if cert_path and key_path:
        ctx.load_cert_chain(cert_path, key_path)
        return ctx, None

    bind_host = host if host not in ("0.0.0.0", "::") else "localhost"
    cert_pem, key_pem = generate_self_signed_cert(bind_host)

    cert_fd, cert_tmp = tempfile.mkstemp(suffix=".pem")
    key_fd, key_tmp = tempfile.mkstemp(suffix=".pem")
    try:
        os.write(cert_fd, cert_pem)
        os.close(cert_fd)
        os.write(key_fd, key_pem)
        os.close(key_fd)
        ctx.load_cert_chain(cert_tmp, key_tmp)
    finally:
        os.unlink(cert_tmp)
        os.unlink(key_tmp)

    return ctx, cert_pem


def make_client_ssl_context(
    ca_cert_path: Optional[str] = None,
    no_verify: bool = False,
) -> ssl.SSLContext:
    """Create a client-side SSLContext.

    Args:
        ca_cert_path: Path to a CA certificate PEM file used to verify the
                      server. Pass the server's self-signed cert here.
        no_verify:    Disable certificate verification entirely. Convenient
                      for quick local use but removes certificate authenticity
                      guarantees (transport is still encrypted).
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2

    if no_verify:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    elif ca_cert_path:
        ctx.load_verify_locations(ca_cert_path)
    else:
        ctx.load_default_certs()

    return ctx
