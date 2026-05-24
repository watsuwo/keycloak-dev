terraform {
  required_version = ">= 1.5"
  required_providers {
    keycloak = {
      source  = "keycloak/keycloak"
      version = "~> 5.0"
    }
  }
}

provider "keycloak" {
  client_id     = "admin-cli"
  username      = "admin"
  password      = var.keycloak_admin_password
  url           = var.keycloak_url
  initial_login = false
}

resource "keycloak_realm" "this" {
  realm                    = "example-customer"
  enabled                  = true
  display_name             = "Example Customer"
  ssl_required             = "external"
  registration_allowed     = false
  login_with_email_allowed = true
  verify_email             = false
  reset_password_allowed   = true
  duplicate_emails_allowed = false
}

module "web_app" {
  source              = "../../../modules/client-confidential"
  realm_id            = keycloak_realm.this.id
  client_id           = "web-app"
  name                = "Example Customer Web App"
  valid_redirect_uris = ["http://localhost:3000/*"]
  web_origins         = ["http://localhost:3000"]
  client_secret       = var.web_app_client_secret
  extra_config = {
    "post.logout.redirect.uris" = "http://localhost:3000"
    "access.token.lifespan"     = "300"
  }
}

module "spa_frontend" {
  source              = "../../../modules/client-public-spa"
  realm_id            = keycloak_realm.this.id
  client_id           = "spa-frontend"
  name                = "Example Customer SPA"
  valid_redirect_uris = ["http://localhost:3001/*"]
  web_origins         = ["http://localhost:3001", "+"]
  extra_config = {
    "post.logout.redirect.uris" = "http://localhost:3001"
    "access.token.lifespan"     = "300"
  }
}

module "batch_worker" {
  source        = "../../../modules/client-service-account"
  realm_id      = keycloak_realm.this.id
  client_id     = "batch-worker"
  name          = "Example Customer Batch Worker"
  client_secret = var.batch_worker_client_secret
}
