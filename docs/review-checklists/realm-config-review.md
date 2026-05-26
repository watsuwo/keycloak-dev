# Realm 設定 (Terraform) レビュー観点チェックリスト

`terraform/environments/<案件>/` への変更 PR をレビューするときの観点。
管理コンソール設定はセキュリティ・運用に直結するため、SPI 以上に細かく見る。

> PR著者の自己レビューにも使える。

---

## 1. PR description / コンテキスト

- [ ] **必須** PR description に **「なぜこの設定変更か」** が書かれている
  - 「顧客要望 #123」「監査指摘対応」「新機能ロールアウト準備」等
- [ ] **必須** **影響範囲** (どのRealm/Client/Userに影響するか) が明示
- [ ] **必須** **`terraform plan` の出力** が PR に添付 (またはGitHub Actions等で自動表示)
  - + / ~ / - の各リソースを目視確認

---

## 2. Realm 設定

- [ ] **必須** `ssl_required` が **本番では `external` 以上** (devは `none` でも可)
- [ ] **必須** `verify_email`, `registration_allowed`, `reset_password_allowed` の設定が要件と合っている
- [ ] **必須** トークン期限が妥当
  - Access Token: 5-15分が一般的
  - Refresh Token: 30分-数時間
  - SSO Session Idle / Max: 業務時間を考慮
- [ ] **必須** ブルートフォース保護が有効 (本番)
- [ ] **推奨** Realm-level Required Actions が想定通り

---

## 3. Clients

- [ ] **必須** Client種別 (confidential / public / service-account) が用途と合っている
  - サーバーサイドWebアプリ → confidential
  - SPA / モバイル → public (PKCE必須)
  - Service-to-Service → service-account
- [ ] **必須** `direct_access_grants_enabled` は **本番では基本 false**
  - true にする場合は理由を PR description に明示 (テスト用クライアントを誤って本番投入していないか)
- [ ] **必須** `valid_redirect_uris` がワイルドカードを濫用していない
  - `https://*` 等の極端なワイルドカード NG
  - `https://app.example.com/*` のような末尾ワイルドカードは妥当
- [ ] **必須** `web_origins` が必要最小限 (CORS許可Origin)
  - `*` NG、明示的にOrigin列挙
- [ ] **必須** `client_secret` が直書きされていない (terraformが自動生成 or 変数経由)
- [ ] **推奨** Client毎の `default_client_scopes` / `optional_client_scopes` が妥当

---

## 4. Roles / Groups

- [ ] **必須** Realm Role と Client Role の使い分けが妥当
- [ ] **必須** デフォルトロール (`default_roles`) に管理者ロールが入っていない
- [ ] **必須** 不要なRoleが削除されている (リネームではなく「削除→新規作成」の場合、既存ユーザーへの影響を確認)
- [ ] **推奨** Group階層が業務組織を反映している (案件のニーズ次第)

---

## 5. Authentication Flow

- [ ] **必須** カスタム Flow を使っている場合、 `topLevel: true, builtIn: false, providerId: "basic-flow"` が正しく設定
- [ ] **必須** カスタム Authenticator (本リポのSPI) を参照している場合、 JAR がデプロイ先に存在する前提が成立しているか
- [ ] **必須** Realm-level Flow Binding (`browserFlow`, `directGrantFlow`, `resetCredentialsFlow` 等) が正しい Flow を指している
- [ ] **推奨** 各 execution の `priority` が10刻みで隙間が空いている (将来挿入余地)

---

## 6. Identity Provider (外部SSO連携)

該当する場合のみ:

- [ ] **必須** Client Secret / OIDC Issuer URL 等の secrets が Terraform variable 経由で注入 (HCLに直書き禁止)
- [ ] **必須** `trust_email` 設定が要件と合っている
  - true: IdP側のemailを信頼してkeycloakに反映 (社内IdP等で OK)
  - false: 別途検証必須 (パブリックIdPでは推奨)
- [ ] **必須** First Broker Login Flow が要件に合っている (自動ユーザー作成 / 既存ユーザー紐づけ等)
- [ ] **推奨** 属性マッパー (`keycloak_oidc_user_attribute_mapper` 等) で必要なclaimを正しくマッピング

---

## 7. SMTP 設定

- [ ] **必須** 本番では実SMTPサーバ (顧客提供 or AWS SES等)、dev/staging は Mailhog or テスト用
- [ ] **必須** SMTP password が secret変数経由
- [ ] **必須** FromアドレスとFrom名が顧客ブランドに合っている

---

## 8. テスト用リソース

- [ ] **必須** テスト用 User (`keycloak_user`) が **本番環境向けの環境変数で apply されない** ようガード
  - 例: `count = var.create_test_users ? 1 : 0`、本番では `create_test_users = false`
- [ ] **必須** テスト用 Client (`testing-only` 等) も同様

---

## 9. シークレット管理

- [ ] **必須** **`.tfvars` ファイルが PR に含まれていない** (`.gitignore` 確認)
- [ ] **必須** `default` 値に本番secret相当の値が入っていない
- [ ] **必須** Terraform outputs で sensitive 指定 (`sensitive = true`)
- [ ] **推奨** Vault / Parameter Store 等の外部secret管理との連携が将来検討事項として TODO/Issue 化

---

## 10. State管理

- [ ] **必須** 本番環境は remote backend (S3 + DynamoDB等) を使っているか
- [ ] **必須** State ファイル (`*.tfstate`) が PR に混入していない
- [ ] **必須** workspaces (`terraform workspace`) で環境分離されているか、または環境別 backend 設定
- [ ] **推奨** state lock が有効

---

## 11. モジュール化

- [ ] **必須** **既存 module を使えるところで inline 実装になっていない**
  - `terraform/modules/client-confidential` がある → confidential client は module 経由
- [ ] **推奨** 新たに module 化したくなった場合、PR description で理由と再利用範囲を明示
- [ ] **推奨** module の variables/outputs に description が記述されている

---

## 12. terraform plan / apply 検証

- [ ] **必須** `terraform plan` で意図しない destroy が含まれていない
  - リネーム時の destroy/create に注意 (`moved` block で対応可能)
- [ ] **必須** dev環境で `make tf-test` (apply → 検証 → destroy) がgreen
- [ ] **推奨** staging で `terraform plan` を実行してdiffを確認
- [ ] **推奨** **影響度の高い変更** (Realm削除、Client secret regenerate, default flow切替) は事前に関係者承認

---

## 13. ドキュメント同期

- [ ] **必須** 設定変更が顧客への影響 (ログイン挙動・必要パスワードルール等) を伴う場合、顧客向けに告知が必要か検討
- [ ] **推奨** `docs/case-spec.md` の対応セクションが更新されている (案件リポの場合)
- [ ] **推奨** 新 module を追加した場合 [docs/specs/task-specs/01-admin-console-config-template.md](../task-specs/01-admin-console-config-template.md) に記入欄追加

---

## 14. リスク評価

PR著者と一緒に判断:

| リスクレベル | 判断基準 | 必要なレビュー |
| --- | --- | --- |
| 低 | dev/staging 限定、Realm削除なし | ジュニア相互レビュー可 |
| 中 | 本番反映、Client追加/設定変更 | 熟練者1名レビュー |
| **高** | Realm削除、Flow切替、IdP連携追加、Secret regenerate | **熟練者2名以上 + 顧客承認** |

---

## レビュアー向けの心構え

- **Terraform plan は必ず目視確認**。「みんな大丈夫って言ってる」で apply しない
- 本番反映前の **staging検証** を省略しない
- 変更の **rollback手順** が PR description にあるか確認 (terraform plan -destroy で戻せるか、手動操作が必要か)
- secrets混入は **絶対に阻止**。混入してしまったら secret rotation + git history rewriting の手順を即実行
