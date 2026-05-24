variable "realm_id" {
  type        = string
  description = "Realm の ID (keycloak_realm.<name>.id を渡す)"
}

variable "client_id" {
  type        = string
  description = "OIDC client_id (例: \"web-app\")"
}

variable "name" {
  type        = string
  description = "Client の表示名 (省略可)"
  default     = null
}

variable "valid_redirect_uris" {
  type        = list(string)
  description = "許可するリダイレクトURI"
  default     = []
}

variable "web_origins" {
  type        = list(string)
  description = "CORS許可Origin。空の場合 valid_redirect_uris から推測されない"
  default     = []
}

variable "standard_flow_enabled" {
  type        = bool
  description = "Authorization Code Flow を許可するか"
  default     = true
}

variable "direct_access_grants_enabled" {
  type        = bool
  description = "Resource Owner Password Credentials Grant を許可するか (通常false、テスト用にtrueにすることがある)"
  default     = false
}

variable "service_accounts_enabled" {
  type        = bool
  description = "Client Credentials Grant (Service Account) を許可するか"
  default     = false
}

variable "client_secret" {
  type        = string
  description = "Client Secret (null で Keycloak 自動生成 — 推奨)"
  default     = null
  sensitive   = true
}

variable "extra_config" {
  type        = map(string)
  description = "Client attributes (例: post.logout.redirect.uris, access.token.lifespan)。Keycloak の Attributes に対応"
  default     = {}
}
