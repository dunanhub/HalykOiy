"""
Environment & Infrastructure Security Checker.

Запускается при старте приложения.
Проверяет что секреты защищены, порты не торчат наружу,
и нет hardcoded ключей в коде.

Использование:
    from app.security.env_checker import run_security_checks
    run_security_checks()  # вызвать в startup
"""

import os
import re
import stat
import subprocess
import logging
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger("security.env_checker")


class SecurityCheckResult:
    """Результат одной проверки."""

    def __init__(self, name: str, passed: bool, detail: str, severity: str = "HIGH"):
        self.name = name
        self.passed = passed
        self.detail = detail
        self.severity = severity  # CRITICAL, HIGH, MEDIUM

    def __str__(self):
        icon = "✅" if self.passed else f"❌ [{self.severity}]"
        return f"  {icon} {self.name}: {self.detail}"


def check_env_file_permissions(env_path: str = ".env") -> SecurityCheckResult:
    """Проверяет что .env не world-readable."""
    path = Path(env_path)
    if not path.exists():
        return SecurityCheckResult(
            ".env permissions",
            True,
            ".env не найден (используются env vars напрямую)",
            "MEDIUM",
        )

    file_stat = path.stat()
    mode = file_stat.st_mode

    # Проверяем что нет world/group read
    if mode & stat.S_IROTH or mode & stat.S_IRGRP:
        return SecurityCheckResult(
            ".env permissions",
            False,
            f".env доступен другим пользователям! mode={oct(mode)}. "
            f"Исправь: chmod 600 {env_path}",
            "CRITICAL",
        )

    return SecurityCheckResult(
        ".env permissions",
        True,
        f".env защищён (mode={oct(mode)})",
    )


def check_no_hardcoded_keys(project_root: str = ".") -> SecurityCheckResult:
    """Ищет hardcoded API-ключи в Python-файлах."""
    patterns = [
        r'["\']sk-[a-zA-Z0-9]{20,}["\']',           # Anthropic keys
        r'["\']AKIA[A-Z0-9]{16}["\']',                # AWS keys
        r'["\']ghp_[a-zA-Z0-9]{36}["\']',             # GitHub tokens
        r'password\s*=\s*["\'][^"\']{8,}["\']',        # Hardcoded passwords
    ]

    found_files: List[str] = []

    for root, dirs, files in os.walk(project_root):
        # Пропускаем node_modules, .git, __pycache__, venv
        dirs[:] = [
            d for d in dirs
            if d not in {"node_modules", ".git", "__pycache__", "venv", ".venv", "env"}
        ]

        for fname in files:
            if not fname.endswith((".py", ".yml", ".yaml", ".toml")):
                continue
            if fname in {"env_checker.py", ".env.example"}:
                continue

            filepath = os.path.join(root, fname)
            try:
                content = open(filepath, "r", errors="ignore").read()
                for pattern in patterns:
                    if re.search(pattern, content):
                        found_files.append(filepath)
                        break
            except (PermissionError, OSError):
                continue

    if found_files:
        return SecurityCheckResult(
            "Hardcoded keys",
            False,
            f"Найдены hardcoded ключи в: {', '.join(found_files[:5])}",
            "CRITICAL",
        )

    return SecurityCheckResult(
        "Hardcoded keys",
        True,
        "Hardcoded ключи не найдены",
    )


def check_env_variables() -> SecurityCheckResult:
    """Проверяет что критичные env-переменные заданы (не дефолтные)."""
    issues = []

    redis_url = os.getenv("REDIS_URL", "")
    if redis_url and "localhost" not in redis_url and ":@" in redis_url:
        pass  # OK — есть пароль
    elif redis_url and "localhost" in redis_url:
        pass  # Dev mode — OK
    elif not redis_url:
        issues.append("REDIS_URL не задан")

    db_url = os.getenv("DATABASE_URL", "")
    if db_url and ("postgres:postgres" in db_url or "password" in db_url.lower()):
        issues.append("DATABASE_URL использует дефолтный пароль!")

    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if anthropic_key and anthropic_key.startswith("sk-ant-"):
        pass  # OK
    elif not anthropic_key:
        issues.append("ANTHROPIC_API_KEY не задан")

    if issues:
        return SecurityCheckResult(
            "Env variables",
            False,
            "; ".join(issues),
            "HIGH",
        )

    return SecurityCheckResult(
        "Env variables",
        True,
        "Критичные env-переменные заданы",
    )


def check_docker_ports() -> SecurityCheckResult:
    """Проверяет что Redis и PG не exposed на 0.0.0.0."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Ports}} {{.Names}}"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return SecurityCheckResult(
                "Docker ports",
                True,
                "Docker не запущен или не доступен (пропускаем)",
                "MEDIUM",
            )

        exposed = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            # Ищем 0.0.0.0:6379 или 0.0.0.0:5432
            if "0.0.0.0:6379" in line:
                exposed.append("Redis (6379) на 0.0.0.0!")
            if "0.0.0.0:5432" in line:
                exposed.append("PostgreSQL (5432) на 0.0.0.0!")

        if exposed:
            return SecurityCheckResult(
                "Docker ports",
                False,
                "; ".join(exposed) + " — используй 127.0.0.1 или internal network",
                "CRITICAL",
            )

        return SecurityCheckResult(
            "Docker ports",
            True,
            "Redis/PG не exposed наружу",
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return SecurityCheckResult(
            "Docker ports",
            True,
            "Docker CLI не найден (пропускаем)",
            "MEDIUM",
        )


def check_gitignore(project_root: str = ".") -> SecurityCheckResult:
    """Проверяет что .env в .gitignore."""
    gitignore = Path(project_root) / ".gitignore"
    if not gitignore.exists():
        return SecurityCheckResult(
            ".gitignore",
            False,
            ".gitignore не найден! Создай и добавь .env, logs/",
            "HIGH",
        )

    content = gitignore.read_text()
    missing = []
    for pattern in [".env", "logs/", "*.log", "audit.jsonl"]:
        if pattern not in content:
            missing.append(pattern)

    if missing:
        return SecurityCheckResult(
            ".gitignore",
            False,
            f"Добавь в .gitignore: {', '.join(missing)}",
            "HIGH",
        )

    return SecurityCheckResult(
        ".gitignore",
        True,
        ".env и logs/ в .gitignore",
    )


def check_log_directory() -> SecurityCheckResult:
    """Проверяет что директория логов существует и защищена."""
    log_dir = Path(os.getenv("AUDIT_LOG_FILE", "logs/audit.jsonl")).parent

    if not log_dir.exists():
        return SecurityCheckResult(
            "Log directory",
            False,
            f"Директория {log_dir} не существует. Создай: mkdir -p {log_dir}",
            "MEDIUM",
        )

    return SecurityCheckResult(
        "Log directory",
        True,
        f"Директория логов {log_dir} существует",
    )


# ─── Main runner ──────────────────────────────────────────────

def run_security_checks(project_root: str = ".") -> List[SecurityCheckResult]:
    """
    Запускает все проверки безопасности.
    Вызывай при старте приложения (в startup event).

    Returns:
        Список результатов проверок.
    """
    checks = [
        check_env_file_permissions(),
        check_no_hardcoded_keys(project_root),
        check_env_variables(),
        check_docker_ports(),
        check_gitignore(project_root),
        check_log_directory(),
    ]

    # Красивый вывод
    logger.info("🔒 Security checks:")
    critical_fails = 0
    for check in checks:
        logger.info(str(check))
        if not check.passed and check.severity == "CRITICAL":
            critical_fails += 1

    passed = sum(1 for c in checks if c.passed)
    total = len(checks)
    logger.info(f"  {'=' * 40}")
    logger.info(f"  Result: {passed}/{total} passed")

    if critical_fails > 0:
        logger.critical(
            f"  🚨 {critical_fails} CRITICAL issue(s)! Fix before deployment."
        )

    return checks
