output "client_uuid" {
  description = "Keycloak内部UUID"
  value       = keycloak_openid_client.this.id
}

output "client_id" {
  description = "OIDC client_id"
  value       = keycloak_openid_client.this.client_id
}

output "service_account_user_id" {
  description = "Service Account の Keycloak User UUID (Role 付与等で参照)"
  value       = keycloak_openid_client.this.service_account_user_id
}

output "client_secret" {
  description = "Client Secret (sensitive)"
  value       = keycloak_openid_client.this.client_secret
  sensitive   = true
}
