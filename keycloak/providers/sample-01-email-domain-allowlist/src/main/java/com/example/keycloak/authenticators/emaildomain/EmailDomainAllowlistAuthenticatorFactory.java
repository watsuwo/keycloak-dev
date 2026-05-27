package com.example.keycloak.authenticators.emaildomain;

import org.keycloak.Config;
import org.keycloak.authentication.Authenticator;
import org.keycloak.authentication.AuthenticatorFactory;
import org.keycloak.models.AuthenticationExecutionModel.Requirement;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.KeycloakSessionFactory;
import org.keycloak.provider.ProviderConfigProperty;
import org.keycloak.provider.ProviderConfigurationBuilder;

import java.util.List;

public class EmailDomainAllowlistAuthenticatorFactory implements AuthenticatorFactory {

    public static final String ID = "email-domain-allowlist-authenticator";

    // Authenticator自体はステートレスなのでシングルトンで使い回せる
    private static final EmailDomainAllowlistAuthenticator SINGLETON =
            new EmailDomainAllowlistAuthenticator();

    @Override
    public String getId() {
        return ID;
    }

    @Override
    public Authenticator create(KeycloakSession session) {
        return SINGLETON;
    }

    @Override
    public String getDisplayType() {
        return "Email Domain Allowlist";
    }

    @Override
    public String getReferenceCategory() {
        return "domain-restriction";
    }

    @Override
    public boolean isConfigurable() {
        return true;
    }

    @Override
    public Requirement[] getRequirementChoices() {
        return new Requirement[]{
                Requirement.REQUIRED,
                Requirement.DISABLED
        };
    }

    @Override
    public boolean isUserSetupAllowed() {
        return false;
    }

    @Override
    public String getHelpText() {
        return "ユーザーのメールアドレスのドメイン部分が許可リストに含まれる場合のみログインを許可します。"
                + "Username/Password等のユーザー特定ステップの後段に配置してください。";
    }

    @Override
    public List<ProviderConfigProperty> getConfigProperties() {
        return ProviderConfigurationBuilder.create()
                .property()
                .name(EmailDomainAllowlistAuthenticator.CONFIG_ALLOWED_DOMAINS)
                .label("許可するドメイン")
                .type(ProviderConfigProperty.MULTIVALUED_STRING_TYPE)
                .helpText("ログインを許可するメールドメイン (例: example.com)。空の場合は制限なし。")
                .add()
                .build();
    }

    @Override
    public void init(Config.Scope config) {
        // no-op
    }

    @Override
    public void postInit(KeycloakSessionFactory factory) {
        // no-op
    }

    @Override
    public void close() {
        // no-op
    }
}
