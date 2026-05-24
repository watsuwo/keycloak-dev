output "client_uuid" {
  description = "Keycloak内部UUID"
  value       = keycloak_openid_client.this.id
}

output "client_id" {
  description = "OIDC client_id"
  value       = keycloak_openid_client.this.client_id
}
