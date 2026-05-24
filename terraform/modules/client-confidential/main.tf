terraform {
  required_providers {
    keycloak = {
      source  = "keycloak/keycloak"
      version = "~> 5.0"
    }
  }
}

resource "keycloak_openid_client" "this" {
  realm_id    = var.realm_id
  client_id   = var.client_id
  name        = var.name
  enabled     = true
  access_type = "CONFIDENTIAL"

  standard_flow_enabled        = var.standard_flow_enabled
  direct_access_grants_enabled = var.direct_access_grants_enabled
  service_accounts_enabled     = var.service_accounts_enabled
  implicit_flow_enabled        = false

  valid_redirect_uris = var.valid_redirect_uris
  web_origins         = var.web_origins

  # client_secret を省略すると Keycloak が自動生成 (推奨)
  client_secret = var.client_secret

  extra_config = var.extra_config
}
