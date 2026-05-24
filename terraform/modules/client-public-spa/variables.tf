variable "realm_id" {
  type        = string
  description = "Realm の ID (keycloak_realm.<name>.id を渡す)"
}

variable "client_id" {
  type        = string
  description = "OIDC client_id (例: \"spa-frontend\")"
}

variable "name" {
  type        = string
  description = "Client の表示名"
  default     = null
}

variable "valid_redirect_uris" {
  type        = list(string)
  description = "許可するリダイレクトURI"
  default     = []
}

variable "web_origins" {
  type        = list(string)
  description = "CORS許可Origin"
  default     = []
}

variable "extra_config" {
  type        = map(string)
  description = "Client attributes"
  default     = {}
}
