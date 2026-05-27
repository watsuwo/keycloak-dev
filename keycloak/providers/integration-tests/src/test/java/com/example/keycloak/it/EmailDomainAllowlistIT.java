package com.example.keycloak.it;

import dasniko.testcontainers.keycloak.KeycloakContainer;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.io.File;
import java.io.FileFilter;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

import static org.assertj.core.api.Assertions.assertThat;

@Testcontainers
@DisplayName("Email Domain Allowlist Authenticator — Integration")
class EmailDomainAllowlistIT {

    private static final String KEYCLOAK_IMAGE = "quay.io/keycloak/keycloak:26.0";
    private static final String REALM = "test-email-domain";
    private static final String CLIENT_ID = "test-client";
    private static final String CLIENT_SECRET = "test-secret";

    @Container
    static final KeycloakContainer KEYCLOAK = new KeycloakContainer(KEYCLOAK_IMAGE)
            .withProviderLibsFrom(loadSpiJars())
            .withRealmImportFile("/test-realm-email-domain.json");
            // デバッグ時はコメントアウトを外してKeycloakコンテナログをstderrに流す:
            // .withEnv("KC_LOG_LEVEL", "INFO,org.keycloak.authentication:DEBUG,org.keycloak.services:DEBUG")
            // .withLogConsumer(of -> System.err.print("[KC] " + of.getUtf8String()));

    private static final HttpClient HTTP = HttpClient.newHttpClient();

    @Test
    @DisplayName("[Smoke] Realm の OIDC well-known が取得できる")
    void smoke_wellKnownReachable() throws Exception {
        String url = baseUrl() + "/realms/" + REALM + "/.well-known/openid-configuration";
        HttpResponse<String> resp = HTTP.send(
                HttpRequest.newBuilder().uri(URI.create(url)).GET().build(),
                HttpResponse.BodyHandlers.ofString());
        assertThat(resp.statusCode())
                .as("well-known URL: %s\nBody: %s", url, resp.body())
                .isEqualTo(200);
        assertThat(resp.body()).contains("token_endpoint");
    }

    @Test
    @DisplayName("許可ドメインのユーザーはDirect Grantでトークン取得できる")
    void allowedDomain_canObtainToken() throws Exception {
        HttpResponse<String> resp = tokenRequest("alice", "password");
        assertThat(resp.statusCode())
                .as("Expected 200 OK but got %d. Body: %s", resp.statusCode(), resp.body())
                .isEqualTo(200);
        assertThat(resp.body()).contains("access_token");
    }

    @Test
    @DisplayName("拒否ドメインのユーザーはDirect Grantでトークン取得が拒否される")
    void disallowedDomain_isRejected() throws Exception {
        HttpResponse<String> resp = tokenRequest("eve", "password");
        assertThat(resp.statusCode())
                .as("Expected 4xx but got %d. Body: %s", resp.statusCode(), resp.body())
                .isBetween(400, 499);
        assertThat(resp.body()).contains("invalid_grant");
    }

    private static String baseUrl() {
        String url = KEYCLOAK.getAuthServerUrl();
        return url.endsWith("/") ? url.substring(0, url.length() - 1) : url;
    }

    private static HttpResponse<String> tokenRequest(String username, String password) throws Exception {
        String form = encode(Map.of(
                "grant_type", "password",
                "client_id", CLIENT_ID,
                "client_secret", CLIENT_SECRET,
                "username", username,
                "password", password));
        HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl() + "/realms/" + REALM + "/protocol/openid-connect/token"))
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString(form))
                .build();
        return HTTP.send(req, HttpResponse.BodyHandlers.ofString());
    }

    private static String encode(Map<String, String> params) {
        return params.entrySet().stream()
                .map(e -> URLEncoder.encode(e.getKey(), StandardCharsets.UTF_8)
                        + "=" + URLEncoder.encode(e.getValue(), StandardCharsets.UTF_8))
                .collect(Collectors.joining("&"));
    }

    private static List<File> loadSpiJars() {
        File dir = new File("target/spi-providers");
        if (!dir.isDirectory()) {
            throw new IllegalStateException(
                    "SPI JAR が見つかりません。'mvn -pl integration-tests verify -am' で先にSPIをビルドしてください: "
                            + dir.getAbsolutePath());
        }
        FileFilter jarFilter = f -> f.isFile()
                && f.getName().endsWith(".jar")
                && !f.getName().endsWith("-sources.jar")
                && !f.getName().endsWith("-javadoc.jar");
        File[] jars = dir.listFiles(jarFilter);
        Objects.requireNonNull(jars, "SPI JAR が読み込めませんでした: " + dir.getAbsolutePath());
        if (jars.length == 0) {
            throw new IllegalStateException("SPI JAR が0件です: " + dir.getAbsolutePath());
        }
        return Arrays.asList(jars);
    }
}
