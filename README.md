# Keycloak on Local Kubernetes

Deploy Keycloak on a local k3d cluster with Terraform, Python, and HTTPS.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 20.10+
- [k3d](https://k3d.io/#installation) 5.x
- [kubectl](https://kubernetes.io/docs/tasks/tools/) 1.27+
- [Terraform](https://developer.hashicorp.com/terraform/install) 1.5+
- [Helm](https://helm.sh/docs/intro/install/) 3.x
- [Python](https://www.python.org/downloads/) 3.11+

## Setup

```bash
git clone https://github.com/muhammadarslan-techsol/keycloak-k8s-terraform-python.git
cd keycloak-k8s-terraform-python
pip install -r requirements.txt
```

Add a hosts entry (one-time):

**Windows** (Admin PowerShell):
```powershell
Add-Content -Path 'C:\Windows\System32\drivers\etc\hosts' -Value "`n127.0.0.1 keycloak.localhost"
```

**Linux / macOS**:
```bash
echo "127.0.0.1 keycloak.localhost" | sudo tee -a /etc/hosts
```

## Usage

```bash
python main.py deploy     # create cluster, generate certs, apply terraform
python main.py status     # show cluster and pod status
python main.py destroy    # tear down everything
```

Admin credentials default to `admin` with a random password (printed on deploy).
Override with environment variables:

```bash
export KEYCLOAK_ADMIN=admin
export KEYCLOAK_ADMIN_PASSWORD=your-password
```

## Access

| | URL |
|---|---|
| Home | https://keycloak.localhost |
| Admin | https://keycloak.localhost/admin |

Browser will warn about the self-signed certificate — safe to proceed.

To trust the certificate system-wide (Admin PowerShell):
```powershell
Import-Certificate -FilePath "<your-clone-path>\certs\tls.crt" -CertStoreLocation Cert:\LocalMachine\Root
```

## Stack

| Component | Image / Tool |
|---|---|
| Keycloak | `quay.io/keycloak/keycloak:26.0` |
| PostgreSQL | `postgres:16-alpine` |
| Ingress | NGINX Ingress Controller (Helm) |
| Cluster | k3d (ports 80/443 mapped) |
| IaC | Terraform (kubernetes + helm providers) |

## Project Structure

```
├── main.py                  # orchestrator (deploy/destroy/status)
├── requirements.txt
├── scripts/
│   ├── cluster.py           # k3d cluster lifecycle
│   ├── tls.py               # self-signed cert generation
│   └── terraform.py         # terraform wrapper
├── terraform/
│   ├── providers.tf
│   ├── variables.tf
│   ├── main.tf              # all k8s resources
│   └── outputs.tf
└── certs/                   # generated at deploy (git-ignored)
```

## Notes

- Add `keycloak.localhost` to your hosts file before deploying.
- Traefik is disabled in k3d; NGINX Ingress handles TLS.
- Keycloak runs in `start-dev` mode using `quay.io/keycloak/keycloak:26.0`.
- PostgreSQL uses `emptyDir` — data is lost on pod restart.
- Terraform state is git-ignored.

## Troubleshooting

**Port 80/443 in use** — stop conflicting services or change port mappings in `scripts/cluster.py`.

**`keycloak.localhost` not resolving** — check your hosts file entry.

**Keycloak pod failing** — inspect with:
```bash
kubectl get pods -n keycloak
kubectl logs -n keycloak <pod-name>
```

**Certificate problems** — delete `certs/` and redeploy.

## License

MIT — see [LICENSE](LICENSE).
