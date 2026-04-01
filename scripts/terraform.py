import os
import subprocess

TF_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "terraform")


def run_tf(args, env=None):
    full_env = {**os.environ, **(env or {})}
    cmd = ["terraform"] + args
    print(f"  -> {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=TF_DIR, env=full_env, check=True)


def init():
    print("[tf] Initializing...")
    run_tf(["init", "-input=false"])


def apply(kubeconfig, cert, key, admin, password, domain="keycloak.localhost"):
    print("[tf] Applying...")
    run_tf([
        "apply", "-auto-approve", "-input=false",
        f"-var=kubeconfig_path={kubeconfig}",
        f"-var=tls_cert_path={cert}",
        f"-var=tls_key_path={key}",
        f"-var=keycloak_admin={admin}",
        f"-var=keycloak_admin_password={password}",
        f"-var=domain={domain}",
    ])
    print("[ok] Apply complete.")


def destroy(kubeconfig, cert, key, admin="admin", password="unused", domain="keycloak.localhost"):
    print("[tf] Destroying...")
    run_tf([
        "destroy", "-auto-approve", "-input=false",
        f"-var=kubeconfig_path={kubeconfig}",
        f"-var=tls_cert_path={cert}",
        f"-var=tls_key_path={key}",
        f"-var=keycloak_admin={admin}",
        f"-var=keycloak_admin_password={password}",
        f"-var=domain={domain}",
    ])
    print("[ok] Destroy complete.")
