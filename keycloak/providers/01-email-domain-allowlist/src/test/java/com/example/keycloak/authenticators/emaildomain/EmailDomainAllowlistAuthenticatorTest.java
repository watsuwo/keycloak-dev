package com.example.keycloak.authenticators.emaildomain;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.keycloak.authentication.AuthenticationFlowContext;
import org.keycloak.authentication.AuthenticationFlowError;
import org.keycloak.models.AuthenticatorConfigModel;
import org.keycloak.models.UserModel;

import java.util.Map;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.RETURNS_DEEP_STUBS;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class EmailDomainAllowlistAuthenticatorTest {

    private EmailDomainAllowlistAuthenticator authenticator;
    private AuthenticationFlowContext context;
    private UserModel user;
    private AuthenticatorConfigModel configModel;

    @BeforeEach
    void setUp() {
        authenticator = new EmailDomainAllowlistAuthenticator();
        // errorResponse() で context.form() などのチェーンを呼ぶため deep stubs を使う
        context = mock(AuthenticationFlowContext.class, RETURNS_DEEP_STUBS);
        user = mock(UserModel.class);
        configModel = mock(AuthenticatorConfigModel.class);

        when(context.getUser()).thenReturn(user);
        when(context.getAuthenticatorConfig()).thenReturn(configModel);
    }

    @Test
    void allowedDomain_succeeds() {
        when(user.getEmail()).thenReturn("alice@example.com");
        when(configModel.getConfig()).thenReturn(Map.of("allowedDomains", "example.com"));

        authenticator.authenticate(context);

        verify(context).success();
    }

    @Test
    void multipleAllowedDomains_secondMatches_succeeds() {
        when(user.getEmail()).thenReturn("bob@corp.example");
        when(configModel.getConfig()).thenReturn(Map.of("allowedDomains", "example.com##corp.example"));

        authenticator.authenticate(context);

        verify(context).success();
    }

    @Test
    void caseInsensitiveMatch_succeeds() {
        when(user.getEmail()).thenReturn("carol@Example.COM");
        when(configModel.getConfig()).thenReturn(Map.of("allowedDomains", "example.com"));

        authenticator.authenticate(context);

        verify(context).success();
    }

    @Test
    void disallowedDomain_fails() {
        when(user.getEmail()).thenReturn("eve@bad.com");
        when(configModel.getConfig()).thenReturn(Map.of("allowedDomains", "example.com##corp.example"));

        authenticator.authenticate(context);

        verify(context).failure(eq(AuthenticationFlowError.ACCESS_DENIED), any());
    }

    @Test
    void noConfig_allowsAll() {
        when(user.getEmail()).thenReturn("anyone@anywhere.com");
        when(context.getAuthenticatorConfig()).thenReturn(null);

        authenticator.authenticate(context);

        verify(context).success();
    }

    @Test
    void emptyConfig_allowsAll() {
        when(user.getEmail()).thenReturn("anyone@anywhere.com");
        when(configModel.getConfig()).thenReturn(Map.of("allowedDomains", ""));

        authenticator.authenticate(context);

        verify(context).success();
    }

    @Test
    void noEmail_failsAsInvalidUser() {
        when(user.getEmail()).thenReturn(null);
        when(configModel.getConfig()).thenReturn(Map.of("allowedDomains", "example.com"));

        authenticator.authenticate(context);

        verify(context).failure(eq(AuthenticationFlowError.INVALID_USER), any());
    }

    @Test
    void noUser_setsAttempted() {
        when(context.getUser()).thenReturn(null);

        authenticator.authenticate(context);

        verify(context).attempted();
    }
}
