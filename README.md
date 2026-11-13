# Eldoria-Client

Официальный репозиторий клиентских файлов и обновлений Minecraft для проекта **Eldoria (TechnoMagic · Minecraft 1.21.1 · NeoForge 21.1.265)**.

## Назначение репозитория

Этот репозиторий используется лаунчером [Eldoria-Launcher](https://github.com/lolihax1/Eldoria-Launcher) для:
- проверки актуальной версии сборки через [`manifest.json`](./manifest.json);
- синхронизации конфигов (`config/`), скриптов KubeJS (`kubejs/`), ресурспаков (`resourcepacks/`) и вспомогательных скриптов запуска (`launcher/`);
- проверки контрольных сумм SHA-512 и автоматической загрузки клиентских модов по ссылкам Modrinth из [`mods-lock.json`](./mods-lock.json).

## Структура

- `manifest.json` — манифест версии сборки, SHA-512 хеши отслеживаемых файлов и список клиентских модов.
- `pack-info.json` — метаданные сборки и требуемая версия NeoForge.
- `mods-lock.json` — список модов сборки с SHA-512 хешами и ссылками на Modrinth CDN.
- `config/` — конфигурация модов и квестов TechnoMagic.
- `kubejs/` — клиентские/серверные скрипты, измерения и ассеты сборки.
- `launcher/` — Python-мост запуска клиента и базовый список серверов.

## Обновление манифеста

После изменения конфигов, скриптов KubeJS или `mods-lock.json` выполните:

```bash
python launcher/generate-manifest.py
```

Скрипт пересчитает хеши всех отслеживаемых файлов и обновит `manifest.json`.
