"""
下载器纯函数单元测试
只测不联网、不碰数据库的 URL 构造/规范化/安全校验/镜像/SSH 通道逻辑。
"""
import pytest

from pathlib import Path
from app.services import downloader_service as ds


# ---------- URL 构造 ----------

def test_build_zip_url():
    assert ds.build_zip_url("octocat", "Hello-World") == \
        "https://codeload.github.com/octocat/Hello-World/zip/refs/heads/main"
    assert ds.build_zip_url("o", "r", "dev") == \
        "https://codeload.github.com/o/r/zip/refs/heads/dev"


def test_build_readme_url():
    assert ds.build_readme_url("o", "r") == \
        "https://raw.githubusercontent.com/o/r/main/README.md"
    assert ds.build_readme_url("o", "r", "dev") == \
        "https://raw.githubusercontent.com/o/r/dev/README.md"


def test_build_clone_url():
    assert ds.build_clone_url("o", "r") == "https://github.com/o/r.git"
    assert ds.build_clone_url("o", "r", use_http=False) == "git@github.com:o/r.git"


# ---------- 文件名净化 ----------

def test_safe_filename_removes_invalid():
    assert "/" not in ds._safe_filename("a/b")
    assert "\\" not in ds._safe_filename("a\\b")
    assert ".." not in ds._safe_filename("..")
    assert ":" not in ds._safe_filename("a:b")
    assert "?" not in ds._safe_filename("a?b")


def test_safe_filename_whitespace_trim_and_fallback():
    assert ds._safe_filename("  hello  ") == "hello"
    assert ds._safe_filename("") == "download"
    # 仅含非法字符时，分隔符被替换为下划线，且不留任何非法字符
    s = ds._safe_filename("://:*?\"|<>")
    assert all(c not in '<>:"|?*' for c in s)
    assert s.strip()


# ---------- 链接规范化（archive -> codeload 直链） ----------

def test_normalize_archive_to_codeload():
    got = ds._normalize_download_url(
        "https://github.com/t/p/archive/refs/heads/main.zip")
    assert got == "https://codeload.github.com/t/p/zip/refs/heads/main"
    # 不带 .zip 后缀 / 结尾斜杠也归一
    got2 = ds._normalize_download_url(
        "http://github.com/t/p/archive/refs/heads/dev/")
    assert got2 == "https://codeload.github.com/t/p/zip/refs/heads/dev"


def test_normalize_returns_unchanged_for_other_urls():
    u = "https://codeload.github.com/t/p/zip/refs/heads/main"
    assert ds._normalize_download_url(u) == u
    u2 = "https://raw.githubusercontent.com/o/r/main/README.md"
    assert ds._normalize_download_url(u2) == u2
    assert ds._normalize_download_url("") == ""


# ---------- 安全校验（防 SSRF/路径注入） ----------

@pytest.mark.parametrize("url", [
    "https://github.com/o/r",
    "https://codeload.github.com/o/r/zip/refs/heads/main",
    "https://raw.githubusercontent.com/o/r/main/README.md",
    "https://api.github.com/repos/o/r",
    "https://objects.githubusercontent.com/x",
    "https://release-assets.githubusercontent.com/a.zip",
])
def test_sanitize_allows_github_domains(url):
    assert ds._sanitize_url(url) == url


@pytest.mark.parametrize("url", [
    "https://example.com/o/r",
    "http://github.com/o/r",  # 明文 HTTP 一律拒绝
    "ftp://github.com/o/r",
    "javascript:alert(1)",
    "https://ghfast.top/https://github.com/o/r",
    "git@github.com:o/r.git",
])
def test_sanitize_rejects_non_github(url):
    with pytest.raises(ValueError):
        ds._sanitize_url(url)


def test_sanitize_empty_returns_empty():
    assert ds._sanitize_url("") == ""


# ---------- 直连地址判定 ----------

def test_is_direct_github_url():
    assert ds.is_direct_github_url("https://github.com/o/r.git")
    assert ds.is_direct_github_url("git@github.com:o/r.git")
    assert not ds.is_direct_github_url("https://codeload.github.com/o/r")
    assert not ds.is_direct_github_url("https://ghfast.top/https://github.com/o/r")


# ---------- 镜像拼接 ----------

def test_apply_mirror_with_github_origin():
    got = ds.apply_mirror("https://github.com/o/r.git",
                          "https://ghfast.top/https://github.com")
    assert got == "https://ghfast.top/https://github.com/o/r.git"


def test_apply_mirror_trims_trailing_slash():
    got = ds.apply_mirror("https://github.com/o/r.git", "https://ghfast.top/")
    assert got == "https://ghfast.top/o/r.git"


def test_apply_mirror_keeps_ssh_unchanged():
    for u in ("git@github.com:o/r.git", "ssh://git@ssh.github.com:443/o/r.git"):
        assert ds.apply_mirror(u, "https://ghfast.top/") == u


def test_apply_mirror_without_mirror_returns_url():
    u = "https://github.com/o/r.git"
    assert ds.apply_mirror(u, "") == u
    assert ds.apply_mirror(u, "  ") == u
    assert ds.apply_mirror(u, None) == u


# ---------- 全局镜像回退列表 ----------

def test_load_clone_mirrors_split_and_strip(monkeypatch):
    monkeypatch.setenv("GITHUB_CLONE_MIRRORS", "a/,  b /, ,c")
    assert ds.load_clone_mirrors() == ["a", "b", "c"]


def test_load_clone_mirrors_empty(monkeypatch):
    monkeypatch.delenv("GITHUB_CLONE_MIRRORS", raising=False)
    assert ds.load_clone_mirrors() == []


# ---------- SSH 备用通道（ssh.github.com:443） ----------

def test_build_ssh443_url_from_https():
    got = ds._build_ssh443_url("https://github.com/o/r")
    assert got == "ssh://git@ssh.github.com:443/o/r.git"
    # 已带 .git 不重复
    assert ds._build_ssh443_url("https://github.com/o/r.git") == \
        "ssh://git@ssh.github.com:443/o/r.git"


def test_build_ssh443_url_returns_none_for_non_origin():
    assert ds._build_ssh443_url("git@github.com:o/r.git") is None
    assert ds._build_ssh443_url("ssh://x@y:443/o/r.git") is None
    assert ds._build_ssh443_url("https://codeload.github.com/o/r") is None
    assert ds._build_ssh443_url("https://github.com/single") is None


# ---------- 私钥定位 ----------

def test_locate_ssh_private_key_from_env(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "nohome"))
    key = tmp_path / "id_test"
    key.write_text("private")
    monkeypatch.setenv("GITHUB_SSH_KEY", str(key))
    assert ds._locate_ssh_private_key() == str(key)


def test_locate_ssh_private_key_returns_empty_when_absent(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "nohome"))
    monkeypatch.delenv("GITHUB_SSH_KEY", raising=False)
    assert ds._locate_ssh_private_key() == ""


# ---------- sshCommand 装配 ----------

def test_ssh_command_with_key(monkeypatch):
    monkeypatch.setattr(ds, "_locate_ssh_private_key", lambda: "K:\\ssh\\id_ed25519")
    cmd = ds._ssh_clone_command()
    assert "accept-new" in cmd
    assert '-i "K:\\ssh\\id_ed25519"' in cmd
    assert "IdentitiesOnly=yes" in cmd


def test_ssh_command_without_key(monkeypatch):
    monkeypatch.setattr(ds, "_locate_ssh_private_key", lambda: "")
    cmd = ds._ssh_clone_command()
    assert "-i" not in cmd
    assert "IdentitiesOnly" not in cmd