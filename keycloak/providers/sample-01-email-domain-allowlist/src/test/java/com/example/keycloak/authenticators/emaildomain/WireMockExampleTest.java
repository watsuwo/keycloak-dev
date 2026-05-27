package com.example.keycloak.authenticators.emaildomain;

import com.github.tomakehurst.wiremock.junit5.WireMockExtension;
import com.github.tomakehurst.wiremock.junit5.WireMockRuntimeInfo;
import com.github.tomakehurst.wiremock.junit5.WireMockTest;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.RegisterExtension;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

import static com.github.tomakehurst.wiremock.client.WireMock.*;
import static com.github.tomakehurst.wiremock.core.WireMockConfiguration.wireMockConfig;
import static org.assertj.core.api.Assertions.assertThat;

/**
 * WireMock 単体テスト利用パターン集。
 *
 * 外部HTTP APIを呼ぶSPIを書く際のテンプレートとして使うこと。
 * 実際のSPIクラスを作ったら、このファイルと同じ要領でテストを書き、このファイルは削除してよい。
 *
 * 主なパターン:
 *   1. @WireMockTest — テストメソッドごとにランダムポートで自動起動/停止 (最シンプル)
 *   2. @RegisterExtension — クラス単位やカスタム設定が必要な場合
 */
class WireMockExampleTest {

    // ----------------------------------------------------------------
    // パターン1: @WireMockTest アノテーション
    //   - クラスに付けるとランダムポートのWireMockサーバが1つ立つ
    //   - テストメソッドの引数 WireMockRuntimeInfo でベースURLを受け取る
    //   - 各テスト後にスタブは自動リセットされる
    // ----------------------------------------------------------------

    @Nested
    @WireMockTest
    @DisplayName("@WireMockTest — 基本パターン")
    class AnnotationStyle {

        @Test
        @DisplayName("GETレスポンスをスタブして呼び出せる")
        void stub_get(WireMockRuntimeInfo wm) throws Exception {
            // --- Arrange ---
            stubFor(get("/api/users/alice")
                    .willReturn(okJson("""
                            {"id":"alice","email":"alice@example.com","active":true}
                            """)));

            // --- Act --- (実際のSPIではここでSPIクラスのメソッドを呼ぶ)
            var response = httpGet(wm.getHttpBaseUrl() + "/api/users/alice");

            // --- Assert ---
            assertThat(response.statusCode()).isEqualTo(200);
            assertThat(response.body()).contains("alice@example.com");

            // リクエストが実際に届いたかを検証
            verify(1, getRequestedFor(urlEqualTo("/api/users/alice")));
        }

        @Test
        @DisplayName("POSTリクエストのボディマッチング")
        void stub_post_with_body_matching(WireMockRuntimeInfo wm) throws Exception {
            stubFor(post("/api/token/verify")
                    .withRequestBody(matchingJsonPath("$.token"))
                    .willReturn(okJson("""
                            {"valid":true,"subject":"alice"}
                            """)));

            var response = httpPost(
                    wm.getHttpBaseUrl() + "/api/token/verify",
                    """
                    {"token":"eyJhbGciOiJSUzI1NiJ9..."}
                    """);

            assertThat(response.statusCode()).isEqualTo(200);
            assertThat(response.body()).contains("\"valid\":true");
        }

        @Test
        @DisplayName("404や401などエラーレスポンスをスタブできる")
        void stub_error_response(WireMockRuntimeInfo wm) throws Exception {
            stubFor(get("/api/users/unknown")
                    .willReturn(aResponse()
                            .withStatus(404)
                            .withHeader("Content-Type", "application/json")
                            .withBody("""
                                    {"error":"user_not_found"}
                                    """)));

            var response = httpGet(wm.getHttpBaseUrl() + "/api/users/unknown");

            assertThat(response.statusCode()).isEqualTo(404);
        }

        @Test
        @DisplayName("リクエストヘッダーのマッチング (Authorization Bearer等)")
        void stub_with_header_matching(WireMockRuntimeInfo wm) throws Exception {
            stubFor(get("/api/me")
                    .withHeader("Authorization", matching("Bearer .+"))
                    .willReturn(okJson("""
                            {"id":"alice"}
                            """)));

            var response = HTTP.send(
                    HttpRequest.newBuilder()
                            .uri(URI.create(wm.getHttpBaseUrl() + "/api/me"))
                            .header("Authorization", "Bearer test-token")
                            .GET()
                            .build(),
                    HttpResponse.BodyHandlers.ofString());

            assertThat(response.statusCode()).isEqualTo(200);
            // ヘッダーが一致しない場合は 404 になることも確認しておくと堅牢
        }

        @Test
        @DisplayName("シナリオ: 1回目は200、2回目は401 (トークン失効など)")
        void stub_scenario_token_expiry(WireMockRuntimeInfo wm) throws Exception {
            // Stateful Behaviour — シナリオ名で状態遷移を定義
            stubFor(get("/api/resource")
                    .inScenario("token-expiry")
                    .whenScenarioStateIs("Started")
                    .willReturn(okJson("""
                            {"data":"secret"}
                            """))
                    .willSetStateTo("token-expired"));

            stubFor(get("/api/resource")
                    .inScenario("token-expiry")
                    .whenScenarioStateIs("token-expired")
                    .willReturn(aResponse().withStatus(401)));

            assertThat(httpGet(wm.getHttpBaseUrl() + "/api/resource").statusCode()).isEqualTo(200);
            assertThat(httpGet(wm.getHttpBaseUrl() + "/api/resource").statusCode()).isEqualTo(401);
        }

        @Test
        @DisplayName("呼び出し回数の検証")
        void verify_call_count(WireMockRuntimeInfo wm) throws Exception {
            stubFor(post("/api/notify").willReturn(noContent()));

            httpPost(wm.getHttpBaseUrl() + "/api/notify", "{}");
            httpPost(wm.getHttpBaseUrl() + "/api/notify", "{}");

            // ちょうど2回呼ばれたことを検証
            verify(2, postRequestedFor(urlEqualTo("/api/notify")));
            // 一度も呼ばれていないエンドポイントの検証
            verify(0, getRequestedFor(urlEqualTo("/api/never-called")));
        }
    }

    // ----------------------------------------------------------------
    // パターン2: @RegisterExtension
    //   - クラス単位でサーバを共有したい場合や固定ポートを使う場合
    //   - static にすると @BeforeAll と同じライフサイクル (クラス内で1つのサーバ)
    //   - インスタンスフィールドにすると各テストで独立したサーバ
    // ----------------------------------------------------------------

    @Nested
    @DisplayName("@RegisterExtension — カスタム設定パターン")
    class ExtensionStyle {

        // @Nested クラスは static メンバーを持てないため、インスタンスフィールドにする。
        // テストメソッドごとに独立したサーバが起動/停止する。
        @RegisterExtension
        WireMockExtension wm = WireMockExtension.newInstance()
                .options(wireMockConfig()
                        .dynamicPort()
                        // 必要ならここで追加設定 (e.g., .withRootDirectory("src/test/resources/wiremock"))
                )
                .build();

        @Test
        @DisplayName("WireMockExtension から直接 stubFor を呼べる")
        void use_extension_directly() throws Exception {
            wm.stubFor(get("/api/status")
                    .willReturn(okJson("""
                            {"status":"ok"}
                            """)));

            var response = httpGet(wm.baseUrl() + "/api/status");

            assertThat(response.statusCode()).isEqualTo(200);
            assertThat(response.body()).contains("ok");
        }
    }

    // ----------------------------------------------------------------
    // ヘルパー (テスト用の薄いHTTPクライアントラッパー)
    // 実際のSPIテストでは SPI クラス自体を呼ぶので不要
    // ----------------------------------------------------------------

    private static final HttpClient HTTP = HttpClient.newHttpClient();

    private static HttpResponse<String> httpGet(String url) throws Exception {
        return HTTP.send(
                HttpRequest.newBuilder().uri(URI.create(url)).GET().build(),
                HttpResponse.BodyHandlers.ofString());
    }

    private static HttpResponse<String> httpPost(String url, String body) throws Exception {
        return HTTP.send(
                HttpRequest.newBuilder()
                        .uri(URI.create(url))
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(body))
                        .build(),
                HttpResponse.BodyHandlers.ofString());
    }
}
