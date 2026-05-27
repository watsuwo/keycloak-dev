# runbooks/ — 運用手順

定型運用作業の手順書置き場。「これどうやるんだっけ?」を即引きできるように。

## 一覧

| 手順書 | 状況 | 使うとき |
| --- | --- | --- |
| [realm-export-import.md](realm-export-import.md) | ✅ あり | 稼働中Realmのバックアップ・スナップショット取得 |
| [keycloak-upgrade.md](keycloak-upgrade.md) | ✅ あり | Keycloakバージョンアップ作業 |
| terraform-workflow.md | 🚧 未整備 | 案件のTerraform実運用 (apply/destroy/state管理) |
| deployment.md | 🚧 未整備 | ステージング/本番デプロイ全体手順 |
| incident-response.md | 🚧 未整備 | 本番障害時の対応 |
| customer-handover.md | 🚧 未整備 | 案件完了時の顧客への引き渡し |

新しい運用作業が発生したら、ここに手順書を追加する。

## 書式

各runbookは以下の構成にすると引きやすい:

1. **目的** — いつ使うか
2. **前提条件** — 環境・権限・ツール
3. **手順** — 番号付きで具体的コマンド込み
4. **検証** — 終わったかどうかの確認方法
5. **トラブルシューティング** — よくあるエラー
6. **ロールバック** — 戻したいとき
