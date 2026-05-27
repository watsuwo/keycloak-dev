# docs/specs/ — 仕様書 (Specifications)

このディレクトリは **仕様書駆動開発 (SDD)** で扱う spec ファイルを集約しています。各ファイルは YAML frontmatter で `spec_id` を持ち、`make spec-validate` で機械検証されます。

## 構成

```
docs/specs/
├── README.md                              このファイル
├── specs-guide.md                         frontmatter スキーマ + spec_id 命名規則 (リファレンス)
├── case-spec-template.md                  TEMPLATE-CASE-SPEC — 案件全体の要件入力テンプレ
├── patterns/                              PATTERN-* — 再利用可能パターンのカタログ
│   └── 01-email-domain-allowlist.md         PATTERN-AUTH-DOMAIN-ALLOWLIST
└── task-specs/                            TEMPLATE-TASK-* — 作業タイプ別の入力テンプレ
    └── 01-admin-console-config-template.md  TEMPLATE-TASK-ADMIN-CONSOLE
```

## spec の4分類

| 接頭辞 | 配置 | 用途 |
| --- | --- | --- |
| `PATTERN-` | `patterns/` | 動く実例 + レシピ (再利用ブロック) |
| `TEMPLATE-` | `case-spec-template.md` / `task-specs/` | フィルイン雛形 |
| `CASE-` | (顧客リポ側 `docs/case-spec.md`) | 実案件全体の要件 |
| `TASK-` | (顧客リポ側 `docs/specs/task-specs/*.md`) | 実案件の作業単位 |

雛形リポには `PATTERN-` と `TEMPLATE-` だけが存在。`CASE-` `TASK-` は顧客リポで作成されます。

## 使い方

```bash
# spec の検証 (frontmatter 整合性 + 参照パス実在)
make spec-validate

# 詳細仕様
cat docs/specs/specs-guide.md
```

新しい spec を書くとき・既存 spec を更新するときは [specs-guide.md](specs-guide.md) を参照してください。

## 関連

- [docs/architecture.md ADR-012](../architecture.md) — SDD導入の判断記録
- [scripts/validate-specs.py](../../scripts/validate-specs.py) — 検証スクリプト
- [docs/specs/specs-guide.md](specs-guide.md) — 詳細リファレンス
