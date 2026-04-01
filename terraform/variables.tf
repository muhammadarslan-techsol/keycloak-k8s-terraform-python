variable "kubeconfig_path" {
  type = string
}

variable "domain" {
  type    = string
  default = "keycloak.localhost"
}

variable "tls_cert_path" {
  type = string
}

variable "tls_key_path" {
  type = string
}

variable "keycloak_admin" {
  type      = string
  sensitive = true
}

variable "keycloak_admin_password" {
  type      = string
  sensitive = true
}

variable "namespace" {
  type    = string
  default = "keycloak"
}
