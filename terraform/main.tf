resource "kubernetes_namespace" "keycloak" {
  metadata {
    name = var.namespace
  }
}

resource "kubernetes_secret" "tls" {
  metadata {
    name      = "tls-cert"
    namespace = kubernetes_namespace.keycloak.metadata[0].name
  }
  type = "kubernetes.io/tls"
  data = {
    "tls.crt" = file(var.tls_cert_path)
    "tls.key" = file(var.tls_key_path)
  }
}

resource "kubernetes_secret" "admin" {
  metadata {
    name      = "admin-creds"
    namespace = kubernetes_namespace.keycloak.metadata[0].name
  }
  data = {
    KEYCLOAK_ADMIN          = var.keycloak_admin
    KEYCLOAK_ADMIN_PASSWORD = var.keycloak_admin_password
  }
}

resource "helm_release" "nginx" {
  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  chart            = "ingress-nginx"
  version          = "4.10.1"
  namespace        = "ingress-nginx"
  create_namespace = true
  wait             = true
  timeout          = 300

  set {
    name  = "controller.service.type"
    value = "ClusterIP"
  }
  set {
    name  = "controller.hostPort.enabled"
    value = "true"
  }
  set {
    name  = "controller.hostPort.ports.https"
    value = "443"
  }
  set {
    name  = "controller.hostPort.ports.http"
    value = "80"
  }
}

resource "kubernetes_deployment" "db" {
  metadata {
    name      = "postgres"
    namespace = kubernetes_namespace.keycloak.metadata[0].name
    labels    = { app = "postgres" }
  }

  spec {
    replicas = 1
    selector {
      match_labels = { app = "postgres" }
    }

    template {
      metadata {
        labels = { app = "postgres" }
      }
      spec {
        container {
          name  = "postgres"
          image = "postgres:16-alpine"

          port {
            container_port = 5432
          }

          env {
            name  = "POSTGRES_DB"
            value = "keycloak"
          }
          env {
            name  = "POSTGRES_USER"
            value = "keycloak"
          }
          env {
            name  = "POSTGRES_PASSWORD"
            value = "keycloak-pg-pass"
          }

          volume_mount {
            name       = "data"
            mount_path = "/var/lib/postgresql/data"
          }

          resources {
            requests = { cpu = "250m", memory = "512Mi" }
            limits   = { cpu = "500m", memory = "1Gi" }
          }
        }

        volume {
          name = "data"
          empty_dir {}
        }
      }
    }
  }
}

resource "kubernetes_service" "db" {
  metadata {
    name      = "postgres"
    namespace = kubernetes_namespace.keycloak.metadata[0].name
  }
  spec {
    selector = { app = "postgres" }
    port {
      port        = 5432
      target_port = 5432
    }
    type = "ClusterIP"
  }
}

resource "kubernetes_deployment" "keycloak" {
  metadata {
    name      = "keycloak"
    namespace = kubernetes_namespace.keycloak.metadata[0].name
    labels    = { app = "keycloak" }
  }

  spec {
    replicas = 1
    selector {
      match_labels = { app = "keycloak" }
    }

    template {
      metadata {
        labels = { app = "keycloak" }
      }
      spec {
        container {
          name  = "keycloak"
          image = "quay.io/keycloak/keycloak:26.0"
          args  = ["start-dev"]

          port {
            container_port = 8080
            name           = "http"
          }

          env_from {
            secret_ref {
              name = kubernetes_secret.admin.metadata[0].name
            }
          }

          env {
            name  = "KC_DB"
            value = "postgres"
          }
          env {
            name  = "KC_DB_URL"
            value = "jdbc:postgresql://postgres:5432/keycloak"
          }
          env {
            name  = "KC_DB_USERNAME"
            value = "keycloak"
          }
          env {
            name  = "KC_DB_PASSWORD"
            value = "keycloak-pg-pass"
          }
          env {
            name  = "KC_PROXY_HEADERS"
            value = "xforwarded"
          }
          env {
            name  = "KC_HTTP_ENABLED"
            value = "true"
          }
          env {
            name  = "KC_HOSTNAME"
            value = var.domain
          }
          env {
            name  = "KC_HEALTH_ENABLED"
            value = "true"
          }

          resources {
            requests = { cpu = "250m", memory = "512Mi" }
            limits   = { cpu = "1",    memory = "1Gi" }
          }

          readiness_probe {
            http_get {
              path = "/health/ready"
              port = 9000
            }
            initial_delay_seconds = 60
            period_seconds        = 10
            failure_threshold     = 10
          }
        }
      }
    }
  }

  depends_on = [kubernetes_deployment.db, kubernetes_service.db]
}

resource "kubernetes_service" "keycloak" {
  metadata {
    name      = "keycloak"
    namespace = kubernetes_namespace.keycloak.metadata[0].name
  }
  spec {
    selector = { app = "keycloak" }
    port {
      port        = 80
      target_port = 8080
    }
    type = "ClusterIP"
  }
}

resource "kubernetes_ingress_v1" "keycloak" {
  metadata {
    name      = "keycloak"
    namespace = kubernetes_namespace.keycloak.metadata[0].name
    annotations = {
      "kubernetes.io/ingress.class"                 = "nginx"
      "nginx.ingress.kubernetes.io/ssl-redirect"    = "true"
      "nginx.ingress.kubernetes.io/proxy-body-size" = "10m"
    }
  }

  spec {
    tls {
      hosts       = [var.domain]
      secret_name = kubernetes_secret.tls.metadata[0].name
    }

    rule {
      host = var.domain
      http {
        path {
          path      = "/"
          path_type = "Prefix"
          backend {
            service {
              name = kubernetes_service.keycloak.metadata[0].name
              port { number = 80 }
            }
          }
        }
      }
    }
  }

  depends_on = [kubernetes_deployment.keycloak, helm_release.nginx]
}
