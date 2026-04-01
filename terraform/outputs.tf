output "url" {
  value = "https://${var.domain}"
}

output "admin_url" {
  value = "https://${var.domain}/admin"
}

output "namespace" {
  value = kubernetes_namespace.keycloak.metadata[0].name
}
