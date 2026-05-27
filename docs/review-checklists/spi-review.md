# SPI 実装 レビュー観点チェックリスト

レビュアー (熟練者) が SPI 実装 PR を見るときの観点まとめ。
PR著者も自己レビューに使える。

> 各項目: 「必須 (落とせない)」「推奨 (落としても通すこともある)」を明示

---

## 1. 設計判断

- [ ] **必須** 既存パターンを派生で済まないか確認したか
  - 同じカテゴリ (Authenticator/EventListener等) のパターンが既にあれば、そこから派生 or 拡張で済ませる
  - 全く新規で書いている場合、その理由を PR description に書く
- [ ] **必須** 適切な SPI 種別を選んでいるか
  - 認証フローのステップ → Authenticator
  - 認証フロー後のアクション強制 → Required Action
  - 監査・通知 → Event Listener
  - 外部ユーザーDB → User Storage Provider
  - トークンclaim制御 → Protocol Mapper
- [ ] **推奨** Conditional Authenticator で十分な要件を、わざわざ通常 Authenticator で書いていないか

---

## 2. 命名・構造

- [ ] **必須** ディレクトリ名が `0N-<pattern-name>` 形式
  - N: 2桁連番 (既存最大の次)
  - kebab-case で用途を表す名前
- [ ] **必須** Maven artifactId と ディレクトリ名が一致
- [ ] **必須** Java パッケージ: `com.<org>.keycloak.<spi-type>.<name>` (顧客リポでは `com.<顧客>.keycloak....`)
- [ ] **必須** Factory のID定数 `public static final String ID` で定義、命名は kebab-case
- [ ] **推奨** Factoryクラス名は `<Name>Factory`、Providerクラス名は `<Name>` (例: `EmailDomainAllowlistAuthenticatorFactory` + `EmailDomainAllowlistAuthenticator`)

---

## 3. SPI登録

- [ ] **必須** `src/main/resources/META-INF/services/<Factoryインタフェースの完全名>` ファイルが存在
- [ ] **必須** ファイル内に Factory実装クラスの FQCN が記述
- [ ] **推奨** ファイル末尾に改行が入っている (一部の ServiceLoader が末尾改行を期待する場合あり)

---

## 4. 実装内容

### Authenticator の場合

- [ ] **必須** `requiresUser()` の戻り値が妥当 (前段でユーザー特定が必要なら `true`)
- [ ] **必須** `context.getUser()` が null の場合のハンドリング (`attempted()` で次へ譲るか、`failure()` で確定拒否か)
- [ ] **必須** `context.failure(error, response)` のResponseが **フロー種別に応じたフォーマット** になっているか
  - Direct Grant → JSON `OAuth2ErrorRepresentation`
  - Browser → HTML `context.form().createErrorPage(...)`
  - 検出は `isDirectGrantFlow()` ヘルパーパターン参照 (パターン1)
- [ ] **必須** `configuredFor()` の判定が要件と合っているか (例: per-userの設定が必要なら適切なチェック)
- [ ] **必須** `setRequiredActions()` の挙動 (必要なら Required Action を user にセット)
- [ ] **推奨** Singletonインスタンスでstatelessに保つ (state持つと並行リクエストで壊れる)

### Event Listener の場合

- [ ] **必須** `onEvent(Event)` 内で例外を投げないこと (Keycloak本体への影響を避ける、try-catchで握る)
- [ ] **必須** `onAdminEvent(AdminEvent, boolean)` も実装 (空でもOK、I/F上の責務として明示)
- [ ] **推奨** 重い処理 (外部HTTP等) は非同期化を検討 (認証フロー全体のレイテンシに影響)

### Protocol Mapper の場合

- [ ] **必須** どのClaim Type (String / Long / Boolean等) を出すか明確
- [ ] **必須** ID/Access/UserInfo token のうち どれに含めるかが Factory で適切に設定

---

## 5. 設定UI (Factory.getConfigProperties)

- [ ] **必須** 各 ProviderConfigProperty に `label` と `helpText` が日本語または英語で記述
- [ ] **必須** secret系の値は `secret=true` でマスク表示
- [ ] **推奨** デフォルト値が realistic で安全 (例: 制限フィルタは「制限なし」より「全部許可」がデフォルトの方が事故防止)
- [ ] **推奨** Multivalued の場合は `MULTIVALUED_STRING_TYPE` を使う (内部表現は `##` 区切り)

---

## 6. リソース管理

- [ ] **必須** `close()` メソッドが空 or 適切にクリーンアップ
- [ ] **必須** Factory の `close()` でも同様
- [ ] **必須** 外部接続 (HTTP, DB, etc.) を持つ場合は、Provider per-request か Singleton かを明確化し、必要に応じて connection pool

---

## 7. ログ・エラー処理

- [ ] **必須** ログは `org.jboss.logging.Logger` を使う (Keycloak本体と同じ仕組み)
- [ ] **必須** ログレベル妥当
  - 認証ステップの通過/失敗: DEBUG or INFO
  - 構成エラー (設定不備): WARN
  - 想定外例外: ERROR
- [ ] **必須** 例外をキャッチして握りつぶしていないか (してるなら理由を明示してログ出力)
- [ ] **推奨** ユーザー入力をログに出す場合は PII (個人情報) 配慮

---

## 8. テストカバレッジ

- [ ] **必須** 単体テスト (`src/test/java/...`) で **全分岐をカバー**
  - 成功パス / 失敗パス / Edge case (null, 空, 不正)
- [ ] **必須** Java IT (`keycloak/providers/integration-tests/.../<Name>IT.java`) で **実Keycloakでの動作確認**
  - smoke (well-known が200) + 成功ケース + 拒否ケース
- [ ] **推奨** ブラウザ画面UIがあれば E2E (`e2e-tests/tests/<name>-browser.spec.ts`) も追加
  - ログイン画面操作 / Authorization Code Flow 全体 / カスタムエラーページ表示
- [ ] **必須** テスト realm JSON (`keycloak/providers/integration-tests/src/test/resources/test-realm-*.json`) が「User Profile 必須属性」の罠を踏んでいない
  - users に `firstName`, `lastName`, `emailVerified: true`, `requiredActions: []` 全部セット

---

## 9. ドキュメント

- [ ] **必須** `keycloak/providers/0N-<name>/CLAUDE.md` がある
  - パターンの目的・配置上の注意・既知の限界
- [ ] **必須** `docs/specs/patterns/0N-<name>.md` のパターンレシピがある
  - **適用判断** (使うべきとき/使わないべきとき)
  - 仕様 / 設定方法 / 派生方法 / 既知の限界 / 過去適用案件
- [ ] **必須** `keycloak/providers/CLAUDE.md` のパターン一覧表が更新されている
- [ ] **推奨** README.md ディレクトリ構成の該当箇所が更新されている

---

## 10. 周辺ファイル

- [ ] **必須** 親 `keycloak/providers/pom.xml` の `<modules>` に新モジュールが追加
- [ ] **必須** 依存バージョンは親POMの dependencyManagement 経由で揃える (個別 module で `<version>` 指定しない)
- [ ] **推奨** ライセンスヘッダ (社内ルールに従う)
- [ ] **必須** secrets を含む `.env` / `.tfvars` 等が PR に混入していない

---

## 11. 動作確認

- [ ] **必須** PR description に `make test-providers / test-integration / test-e2e` の結果がスクショまたは「全green」明記
- [ ] **必須** 管理コンソールで実際に設定 → 認証フロー実行 → 期待動作になることを手動確認 (該当する場合)
- [ ] **推奨** PR description に「手動で何を試したか」(ユーザ・パスワード・期待動作) を残す

---

## 12. 既知の罠を踏んでいないか

[docs/testing.md](../testing.md#既知の罠--集約リスト) の罠リストを再確認:

- [ ] Mockito version は 5.15+ (JDK 24/25 対応)
- [ ] MDEP-187 対応 (integration-tests のcopy-dependencies フェーズ)
- [ ] Direct Grant で `context.failure(error)` 単独呼び出ししていない
- [ ] テストユーザーに `firstName`/`lastName`/`emailVerified`/`requiredActions: []`
- [ ] E2E で OAuth redirect の検証は `waitForRequest` パターン
- [ ] `getAuthServerUrl()` 末尾スラッシュ問題への対処
- [ ] Maven Central に存在する Keycloak バージョン (`keycloak.version`)

---

## レビュアー向けの心構え

- 設計判断 (パターン化・命名・フロー検出) は **将来コスト** に直結する。妥協せずに指摘
- 実装の細部 (空白・コメント) は重要度低。指摘するなら「軽い提案」と明示
- レビュー中に「あ、これは既知の罠だ」と気付いたら **その場で docs/testing.md に追記** することを推奨
- 著者が新人なら **なぜそうあるべきか** を解説するコメントを残す (育成も役割)
