import hashlib
import json
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO_URL = "https://github.com/lolihax1/Eldoria-Client"
RAW_BASE_URL = "https://raw.githubusercontent.com/lolihax1/Eldoria-Client/main/"

TRACKED_TOP_FILES = ["pack-info.json", "mods-lock.json"]
TRACKED_LAUNCHER_FILES = [
    "launcher/electron-bridge.py",
    "launcher/resolve-profile-skin.py",
    "launcher/servers.json",
]
TRACKED_DIRS = ["config", "kubejs", "resourcepacks"]
EXCLUDED_PATHS = {
    "config/sodium-fingerprint.json",
}
MISSING_ONLY_PATHS = {
    "config/sodium-options.json",
    "config/ftbchunks-client.snbt",
    "config/ftblibrary-client.snbt",
    "config/ftbquests-client.snbt",
    "launcher/servers.json",
}
MISSING_ONLY_PREFIXES = (
    "config/jei/",
    "config/jade/",
    "config/brandon3055/",
    "config/mezz_config/",
)


def is_missing_only(rel: str) -> bool:
    return (
        rel in MISSING_ONLY_PATHS
        or rel.startswith(MISSING_ONLY_PREFIXES)
        or (rel.startswith("config/") and rel.endswith("-client.toml"))
    )


def sha512_file(path: pathlib.Path) -> str:
    digest = hashlib.sha512()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files() -> list[dict]:
    entries = []
    seen = set()

    for rel in TRACKED_TOP_FILES + TRACKED_LAUNCHER_FILES:
        p = ROOT / rel
        if p.is_file() and rel not in EXCLUDED_PATHS:
            seen.add(rel)
            entries.append({
                "path": rel,
                "size": p.stat().st_size,
                "sha512": sha512_file(p),
                "mode": "missing" if is_missing_only(rel) else "always",
            })

    for folder in TRACKED_DIRS:
        base = ROOT / folder
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(ROOT).as_posix()
            if rel in EXCLUDED_PATHS or rel in seen or p.name.startswith("."):
                continue
            seen.add(rel)
            entries.append({
                "path": rel,
                "size": p.stat().st_size,
                "sha512": sha512_file(p),
                "mode": "missing" if is_missing_only(rel) else "always",
            })

    entries.sort(key=lambda item: item["path"])
    return entries


def collect_mods() -> list[dict]:
    lock_path = ROOT / "mods-lock.json"
    if not lock_path.is_file():
        return []
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    mods = []
    for mod_id, item in lock.items():
        if item.get("side") == "server":
            continue
        file_info = item.get("file") or {}
        hashes = file_info.get("hashes") or {}
        mods.append({
            "id": mod_id,
            "name": item.get("name", mod_id),
            "slug": item.get("slug", ""),
            "version": item.get("version", ""),
            "side": item.get("side", "both"),
            "filename": file_info.get("filename", ""),
            "size": file_info.get("size", 0),
            "sha512": hashes.get("sha512", ""),
            "url": file_info.get("url", ""),
        })
    mods.sort(key=lambda m: m["filename"].lower())
    return mods


def main():
    pack_info = json.loads((ROOT / "pack-info.json").read_text(encoding="utf-8"))
    version_id = pack_info.get("version", "neoforge-21.1.265")
    loader_version = version_id.replace("neoforge-", "") if version_id.startswith("neoforge-") else version_id
    mods = collect_mods()
    files = collect_files()

    manifest = {
        "schemaVersion": 1,
        "name": pack_info.get("name", "Eldoria TechnoMagic"),
        "packVersion": pack_info.get("packVersion", "0.1.0"),
        "release": pack_info.get("release", "0.1-playtest"),
        "minecraft": pack_info.get("minecraft", "1.21.1"),
        "loader": "neoforge",
        "loaderVersion": loader_version,
        "versionId": version_id,
        "repository": REPO_URL,
        "rawBaseUrl": RAW_BASE_URL,
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "modsCount": len(mods),
        "filesCount": len(files),
        "files": files,
        "mods": mods,
    }

    dest = ROOT / "manifest.json"
    dest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {dest} ({len(files)} files, {len(mods)} client mods)")


if __name__ == "__main__":
    main()
