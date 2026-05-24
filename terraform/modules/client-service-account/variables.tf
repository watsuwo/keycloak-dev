variable "realm_id" {
  type        = string
  description = "Realm の ID"
}

variable "client_id" {
  type        = string
  description = "OIDC client_id (例: \"batch-worker\")"
}

variable "name" {
  type        = string
  description = "Client の表示名"
  default     = null
}

variable "client_secret" {
  type        = string
  description = "Client Secret (null で Keycloak 自動生成 — 推奨)"
  default     = null
  sensitive   = true
}

variable "extra_config" {
  type        = map(string)
  description = "Client attributes"
  default     = {}
}
