terraform {
  required_version = ">= 1.5.0"
  required_providers {
    keycloak = {
      source  = "keycloak/keycloak"
      version = "~> 5.0"
    }
  }
}

provider "keycloak" {
  client_id                = var.keycloak_admin_client_id
  username                 = var.keycloak_admin_username
  password                 = var.keycloak_admin_password
  url                      = var.keycloak_url
  tls_insecure_skip_verify = var.tls_insecure_skip_verify
}

# ----- Realm -----

resource "keycloak_realm" "this" {
  realm        = var.realm_name
  enabled      = true
  display_name = "Example Customer Realm (staging)"

  ssl_required = var.ssl_required

  # ログインで使える方法
  registration_allowed      = false
  reset_password_allowed    = false
  remember_me               = false
  verify_email              = false
  login_with_email_allowed  = true
  duplicate_emails_allowed  = false
}

# ----- Clients -----

module "web_app_client" {
  source = "../../../modules/client-confidential"

  realm_id  = keycloak_realm.this.id
  client_id = "web-app"
  name      = "Web Application"

  # stg environment: staging domain
  valid_redirect_uris = ["https://stg.app.example.com/*"]
  web_origins         = ["https://stg.app.example.com"]

  standard_flow_enabled        = true
  direct_access_grants_enabled = false # production mode: no direct grant
}

module "spa_frontend_client" {
  source = "../../../modules/client-public-spa"

  realm_id  = keycloak_realm.this.id
  client_id = "spa-frontend"
  name      = "SPA Frontend"

  # stg environment: staging domain
  valid_redirect_uris = ["https://stg.spa.example.com/*"]
  web_origins         = ["https://stg.spa.example.com"]
}

module "batch_worker_client" {
  source = "../../../modules/client-service-account"

  realm_id  = keycloak_realm.this.id
  client_id = "batch-worker"
  name      = "Batch Worker"
}
