variable "keycloak_url" {
  type        = string
  description = "Keycloak の base URL (例: https://keycloak.example.com)"
}

variable "keycloak_admin_password" {
  type        = string
  description = "master realm の admin パスワード"
  sensitive   = true
}

variable "web_app_client_secret" {
  type        = string
  description = "web-app client_secret"
  sensitive   = true
}

variable "batch_worker_client_secret" {
  type        = string
  description = "batch-worker client_secret"
  sensitive   = true
}
