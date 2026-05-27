package com.example.keycloak.authenticators.emaildomain;

import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.keycloak.authentication.AuthenticationFlowContext;
import org.keycloak.authentication.AuthenticationFlowError;
import org.keycloak.authentication.Authenticator;
import org.keycloak.models.AuthenticationExecutionModel;
import org.keycloak.models.AuthenticationFlowModel;
import org.keycloak.models.AuthenticatorConfigModel;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.RealmModel;
import org.keycloak.models.UserModel;
import org.keycloak.representations.idm.OAuth2ErrorRepresentation;

import java.util.Arrays;
import java.util.List;

/**
 * ユーザーのメールアドレスのドメインが許可リストに含まれる場合のみログインを許可する。
 * 認証フローでは Username/Password 等で user が解決された後のステップとして使う。
 *
 * 拒否時のレスポンスはフロー種別で出し分ける:
 *   - Direct Grant: OAuth2 JSON エラー ({"error":"invalid_grant", ...}) — 必須、無いとKeycloakが500
 *   - Browser     : context.form().createErrorPage() の HTML エラーページ — UX良好
 */
public class EmailDomainAllowlistAuthenticator implements Authenticator {

    static final String CONFIG_ALLOWED_DOMAINS = "allowedDomains";

    @Override
    public void authenticate(AuthenticationFlowContext context) {
        UserModel user = context.getUser();
        if (user == null) {
            context.attempted();
            return;
        }

        String email = user.getEmail();
        if (email == null || !email.contains("@")) {
            context.failure(AuthenticationFlowError.INVALID_USER,
                    errorResponse(context, "invalid_grant", "メールアドレスが未設定または不正です"));
            return;
        }

        List<String> allowed = readAllowedDomains(context.getAuthenticatorConfig());
        if (allowed.isEmpty()) {
            context.success();
            return;
        }

        String domain = email.substring(email.indexOf('@') + 1).toLowerCase();
        boolean ok = allowed.stream()
                .map(String::toLowerCase)
                .map(String::trim)
                .anyMatch(d -> d.equals(domain));

        if (ok) {
            context.success();
        } else {
            context.failure(AuthenticationFlowError.ACCESS_DENIED,
                    errorResponse(context, "invalid_grant", "このドメインからのログインは許可されていません"));
        }
    }

    @Override
    public void action(AuthenticationFlowContext context) {
        // フォームを表示しないAuthenticatorなのでaction呼び出しは想定しない
    }

    @Override
    public boolean requiresUser() {
        return true;
    }

    @Override
    public boolean configuredFor(KeycloakSession session, RealmModel realm, UserModel user) {
        return true;
    }

    @Override
    public void setRequiredActions(KeycloakSession session, RealmModel realm, UserModel user) {
        // no-op
    }

    @Override
    public void close() {
        // no-op
    }

    private static List<String> readAllowedDomains(AuthenticatorConfigModel config) {
        if (config == null) {
            return List.of();
        }
        String raw = config.getConfig().get(CONFIG_ALLOWED_DOMAINS);
        if (raw == null || raw.isBlank()) {
            return List.of();
        }
        // KeycloakのMULTIVALUED_STRING_TYPEは "##" 区切りで保存される
        return Arrays.asList(raw.split("##"));
    }

    /**
     * フロー種別に応じたエラーレスポンスを作る。
     * Direct GrantではJSON、それ以外 (Browserフロー等) ではHTMLエラーページを返す。
     */
    private static Response errorResponse(AuthenticationFlowContext context,
                                          String oauthError,
                                          String description) {
        if (isDirectGrantFlow(context)) {
            OAuth2ErrorRepresentation err = new OAuth2ErrorRepresentation(oauthError, description);
            return Response.status(Response.Status.UNAUTHORIZED)
                    .entity(err)
                    .type(MediaType.APPLICATION_JSON_TYPE)
                    .build();
        }
        return context.form()
                .setError(description)
                .createErrorPage(Response.Status.FORBIDDEN);
    }

    /**
     * 現在のフローが Realm の directGrantFlow に属しているかを判定する。
     */
    private static boolean isDirectGrantFlow(AuthenticationFlowContext context) {
        AuthenticationExecutionModel exec = context.getExecution();
        if (exec == null || exec.getParentFlow() == null) {
            return false;
        }
        AuthenticationFlowModel directGrantFlow = context.getRealm().getDirectGrantFlow();
        return directGrantFlow != null
                && directGrantFlow.getId().equals(exec.getParentFlow());
    }
}
