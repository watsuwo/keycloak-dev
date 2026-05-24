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

  standard_flow_enabled        = false
  direct_access_grants_enabled = false
  service_accounts_enabled     = true
  implicit_flow_enabled        = false

  valid_redirect_uris = []
  web_origins         = []

  client_secret = var.client_secret
  extra_config  = var.extra_config
}
