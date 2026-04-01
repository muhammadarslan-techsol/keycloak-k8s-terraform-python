#!/usr/bin/env python3

import argparse
import os
import secrets
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))

from scripts.cluster import create_cluster, delete_cluster, get_kubeconfig_path, cluster_exists, CLUSTER_NAME
from scripts.tls import generate_cert
from scripts import terraform as tf

DOMAIN = "keycloak.localhost"
CERT_DIR = os.path.join(os.path.dirname(__file__), "certs")


def get_credentials():
    user = os.environ.get("KEYCLOAK_ADMIN", "admin")
    password = os.environ.get("KEYCLOAK_ADMIN_PASSWORD")
    if not password:
        password = secrets.token_urlsafe(16)
        print(f"[creds] Generated password: {password}")
    return user, password


def check_tools():
    tools = {
        "docker": ["docker", "--version"],
        "k3d": ["k3d", "version"],
        "kubectl": ["kubectl", "version", "--client"],
        "terraform": ["terraform", "--version"],
        "helm": ["helm", "version"],
    }
    missing = []
    for name, cmd in tools.items():
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            missing.append(name)
    if missing:
        print(f"[error] Missing tools: {', '.join(missing)}")
        sys.exit(1)
    print("[ok] All tools found.")


def setup_helm():
    subprocess.run(["helm", "repo", "add", "ingress-nginx",
                    "https://kubernetes.github.io/ingress-nginx"], capture_output=True)
    subprocess.run(["helm", "repo", "update"], capture_output=True, check=True)
    print("[ok] Helm repos updated.")


def deploy():
    print("=" * 55)
    print("  Keycloak on Kubernetes")
    print("=" * 55)

    print("\n[1/6] Checking tools...")
    check_tools()

    print("\n[2/6] Getting credentials...")
    user, password = get_credentials()

    print("\n[3/6] Creating cluster...")
    create_cluster()
    kubeconfig = get_kubeconfig_path()

    print("\n[4/6] Generating TLS certs...")
    cert, key = generate_cert(DOMAIN, CERT_DIR)

    print("\n[5/6] Setting up Helm...")
    setup_helm()

    print("\n[6/6] Running Terraform...")
    tf.init()
    tf.apply(kubeconfig, cert, key, user, password, DOMAIN)

    print("\n" + "=" * 55)
    print(f"  URL:      https://{DOMAIN}")
    print(f"  Admin:    https://{DOMAIN}/admin")
    print(f"  User:     {user}")
    print(f"  Password: {password}")
    print("=" * 55)


def destroy():
    cert = os.path.join(CERT_DIR, "tls.crt")
    key = os.path.join(CERT_DIR, "tls.key")
    user, password = get_credentials()
    try:
        kubeconfig = get_kubeconfig_path()
        tf.init()
        tf.destroy(kubeconfig, cert, key, user, password, DOMAIN)
    except Exception as e:
        print(f"[warn] Terraform destroy failed: {e}")
    delete_cluster()
    print("[ok] Teardown complete.")


def status():
    if cluster_exists():
        print(f"  Cluster '{CLUSTER_NAME}': RUNNING")
    else:
        print(f"  Cluster '{CLUSTER_NAME}': NOT FOUND")
        return

    kubeconfig = get_kubeconfig_path()
    env = {**os.environ, "KUBECONFIG": kubeconfig}

    for resource in ["pods", "ingress"]:
        try:
            r = subprocess.run(
                ["kubectl", "get", resource, "-n", "keycloak", "--no-headers"],
                capture_output=True, text=True, check=True, env=env,
            )
            print(f"\n  {resource}:\n{r.stdout}")
        except subprocess.CalledProcessError:
            print(f"  {resource}: not found")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["deploy", "destroy", "status"])
    args = parser.parse_args()
    {"deploy": deploy, "destroy": destroy, "status": status}[args.action]()


if __name__ == "__main__":
    main()
