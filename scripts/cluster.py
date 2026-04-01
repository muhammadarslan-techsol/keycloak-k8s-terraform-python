import json
import subprocess
import sys
import time

CLUSTER_NAME = "keycloak-local"


def run(cmd, check=True):
    print(f"  -> {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def cluster_exists():
    result = run(["k3d", "cluster", "list", "-o", "json"], check=False)
    if result.returncode != 0:
        return False
    return any(c["name"] == CLUSTER_NAME for c in json.loads(result.stdout))


def create_cluster():
    if cluster_exists():
        print(f"[skip] Cluster '{CLUSTER_NAME}' already exists.")
        return

    print(f"[cluster] Creating '{CLUSTER_NAME}'...")
    run([
        "k3d", "cluster", "create", CLUSTER_NAME,
        "--port", "443:443@loadbalancer",
        "--port", "80:80@loadbalancer",
        "--k3s-arg", "--disable=traefik@server:0",
        "--wait",
    ])
    wait_ready()


def wait_ready(timeout=120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = run(["kubectl", "get", "nodes", "--no-headers"], check=False)
        if r.returncode == 0 and "Ready" in r.stdout:
            print("[ok] Cluster ready.")
            return
        time.sleep(3)
    print("[warn] Timed out waiting for cluster.", file=sys.stderr)


def delete_cluster():
    if not cluster_exists():
        print(f"[skip] Cluster '{CLUSTER_NAME}' not found.")
        return
    run(["k3d", "cluster", "delete", CLUSTER_NAME])
    print("[ok] Cluster deleted.")


def get_kubeconfig_path():
    result = run(["k3d", "kubeconfig", "write", CLUSTER_NAME])
    path = result.stdout.strip()
    patch_kubeconfig(path)
    return path


def patch_kubeconfig(path):
    with open(path, "r") as f:
        content = f.read()
    if "host.docker.internal" in content:
        with open(path, "w") as f:
            f.write(content.replace("host.docker.internal", "127.0.0.1"))
        print("[ok] Patched kubeconfig -> 127.0.0.1")
