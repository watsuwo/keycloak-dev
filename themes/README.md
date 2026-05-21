# themes/

Keycloakの **テーマ** (FreeMarkerテンプレート + CSS/JS + メッセージ) を配置する。`compose.yaml` で `/opt/keycloak/themes/` にマウントされる。

## 構成 (Phase 2以降)

```
themes/
└── <theme-name>/
    ├── login/
    │   ├── theme.properties
    │   ├── login.ftl
    │   ├── resources/
    │   │   ├── css/
    │   │   ├── js/
    │   │   └── img/
    │   └── messages/
    │       ├── messages_en.properties
    │       └── messages_ja.properties
    ├── email/
    ├── account/
    └── admin/
```

## 開発時のキャッシュ

`compose.yaml` で `KC_SPI_THEME_CACHE_THEMES=false` 等を設定済みのため、FTLや静的ファイルの変更はブラウザリロードで反映される。

> 詳細はPhase 2で本ディレクトリ内に専用CLAUDE.mdを追加予定。
