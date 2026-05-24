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
  access_type = "PUBLIC"

  standard_flow_enabled        = true
  direct_access_grants_enabled = false
  service_accounts_enabled     = false
  implicit_flow_enabled        = false

  valid_redirect_uris = var.valid_redirect_uris
  web_origins         = var.web_origins

  extra_config = var.extra_config

  # PKCE 必須 (public client の security baseline)
  pkce_code_challenge_method = "S256"
}
