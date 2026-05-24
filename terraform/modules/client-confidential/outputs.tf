output "client_uuid" {
  description = "Keycloak内部UUID (admin API で参照する際に使う)"
  value       = keycloak_openid_client.this.id
}

output "client_id" {
  description = "OIDC client_id"
  value       = keycloak_openid_client.this.client_id
}

output "client_secret" {
  description = "発行されたClient Secret (sensitive)"
  value       = keycloak_openid_client.this.client_secret
  sensitive   = true
}
