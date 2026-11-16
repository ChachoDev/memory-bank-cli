"""Detect existing code and infer the technology stack of a project.

Inspects root-level marker files, dependency manifests and framework signatures
to build a detailed stack list.  For example, a ``package.json`` that depends on
``react`` yields ``["Node.js", "React"]`` instead of just ``["Node.js"]``.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Final, TypedDict


class ScanResult(TypedDict):
    has_code: bool
    detected_stack: list[str]


# Exact file names in the project root and the stack they reveal.
ROOT_MARKERS: Final[dict[str, str]] = {
    "package.json": "Node.js",
    "tsconfig.json": "TypeScript",
    "deno.json": "Deno",
    "deno.jsonc": "Deno",
    "bun.lockb": "Bun",
    "bun.lock": "Bun",
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "setup.py": "Python",
    "Pipfile": "Python",
    "uv.lock": "uv",
    "Cargo.toml": "Rust",
    "go.mod": "Go",
    "pom.xml": "Java (Maven)",
    "build.gradle": "JVM (Gradle)",
    "build.gradle.kts": "Kotlin (Gradle)",
    "Gemfile": "Ruby",
    "composer.json": "PHP",
    "Package.swift": "Swift",
    "mix.exs": "Elixir",
    "CMakeLists.txt": "C/C++ (CMake)",
    "Makefile": "Make",
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    "compose.yml": "Docker Compose",
    "compose.yaml": "Docker Compose",
}

# Glob patterns in the project root and the stack they reveal.
ROOT_GLOBS: Final[dict[str, str]] = {
    "*.csproj": ".NET",
    "*.sln": ".NET",
    "*.tf": "Terraform",
}

SOURCE_EXTENSIONS: Final = frozenset(
    {
        ".py",
        ".js",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".jsx",
        ".dart",
        ".rs",
        ".go",
        ".java",
        ".kt",
        ".swift",
        ".rb",
        ".php",
        ".cs",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".ex",
        ".exs",
        ".scala",
        ".vue",
        ".svelte",
        ".sh",
        ".sql",
    }
)

IGNORED_DIRS: Final = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        "dist",
        "build",
        "target",
        ".dart_tool",
        ".idea",
        ".vscode",
        "memory-bank",
        ".opencode",
        ".claude",
        ".agents",
        ".junie",
    }
)

MAX_DEPTH: Final = 3

# Framework detection: maps a dependency name (lowercase) to a framework label.
# Only the most common/recognisable frameworks are listed here.
_NPM_FRAMEWORKS: Final[dict[str, str]] = {
    "react": "React",
    "react-dom": "React",
    "next": "Next.js",
    "vue": "Vue",
    "nuxt": "Nuxt",
    "svelte": "Svelte",
    "svelte-kit": "SvelteKit",
    "angular": "Angular",
    "@angular/core": "Angular",
    "express": "Express",
    "fastify": "Fastify",
    "koa": "Koa",
    "nest": "NestJS",
    "@nestjs/core": "NestJS",
    "electron": "Electron",
    "tailwindcss": "Tailwind CSS",
    "webpack": "Webpack",
    "vite": "Vite",
    "eslint": "ESLint",
    "prettier": "Prettier",
    "jest": "Jest",
    "mocha": "Mocha",
    "cypress": "Cypress",
    "playwright": "Playwright",
    "prisma": "Prisma",
    "typeorm": "TypeORM",
    "sequelize": "Sequelize",
    "mongoose": "Mongoose",
    "redux": "Redux",
    "@reduxjs/toolkit": "Redux Toolkit",
    "mobx": "MobX",
    "socket.io": "Socket.IO",
    "graphql": "GraphQL",
    "apollo-server": "Apollo Server",
    "@apollo/server": "Apollo Server",
    "axios": "Axios",
    "three": "Three.js",
    "d3": "D3.js",
    "lodash": "Lodash",
}

_PYPI_FRAMEWORKS: Final[dict[str, str]] = {
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "starlette": "Starlette",
    "tornado": "Tornado",
    "sanic": "Sanic",
    "aiohttp": "aiohttp",
    "pyramid": "Pyramid",
    "celery": "Celery",
    "sqlalchemy": "SQLAlchemy",
    "alembic": "Alembic",
    "pytest": "pytest",
    "numpy": "NumPy",
    "pandas": "Pandas",
    "scikit-learn": "scikit-learn",
    "torch": "PyTorch",
    "tensorflow": "TensorFlow",
    "keras": "Keras",
    "matplotlib": "Matplotlib",
    "streamlit": "Streamlit",
    "gradio": "Gradio",
    "rich": "Rich",
    "click": "Click",
    "typer": "Typer",
    "httpx": "HTTPX",
    "requests": "Requests",
    "pydantic": "Pydantic",
    "uvicorn": "Uvicorn",
    "gunicorn": "Gunicorn",
    "djangorestframework": "Django REST Framework",
    "redis": "Redis",
    "boto3": "AWS SDK (Boto3)",
    "google-cloud": "Google Cloud SDK",
    "pillow": "Pillow",
    "beautifulsoup4": "BeautifulSoup",
    "scrapy": "Scrapy",
    "sphinx": "Sphinx",
    "ruff": "Ruff",
    "black": "Black",
    "mypy": "mypy",
    "pre-commit": "pre-commit",
}

_CARGO_FRAMEWORKS: Final[dict[str, str]] = {
    "actix-web": "Actix Web",
    "axum": "Axum",
    "rocket": "Rocket",
    "tokio": "Tokio",
    "warp": "Warp",
    "serde": "Serde",
    "diesel": "Diesel",
    "sqlx": "SQLx",
    "clap": "Clap",
    "tower": "Tower",
    "hyper": "Hyper",
    "wasm-bindgen": "Wasm-bindgen",
    "tauri": "Tauri",
}

_GO_FRAMEWORKS: Final[dict[str, str]] = {
    "gin-gonic/gin": "Gin",
    "gorilla/mux": "Gorilla Mux",
    "echo": "Echo",
    "fiber": "Fiber",
    "chi": "Chi",
    "gorm": "GORM",
    "grpc": "gRPC",
    "protobuf": "Protocol Buffers",
}

_GRADLE_FRAMEWORKS_RE: Final = re.compile(
    r"""(?:implementation|api|compileOnly|testImplementation)\s*\(?['"]?(?:([a-zA-Z0-9_.-]+):([a-zA-Z0-9_.-]+))['"]?\)?""",
    re.IGNORECASE,
)

_GRADLE_LIB_MAP: Final[dict[str, str]] = {
    "spring-boot-starter-web": "Spring Boot",
    "spring-boot-starter-data-jpa": "Spring Boot",
    "spring-boot-starter-security": "Spring Boot",
    "spring-boot-starter-test": "Spring Boot",
    "spring-webflux": "Spring WebFlux",
    "kotlinx-serialization-json": "Kotlin Serialization",
    "ktor-server-core": "Ktor",
    "ktor-client-core": "Ktor",
    "junit-jupiter": "JUnit 5",
    "mockito-core": "Mockito",
    "hibernate-core": "Hibernate",
    "mybatis": "MyBatis",
    "quarkus-getting-started": "Quarkus",
    "micronaut-http-server-netty": "Micronaut",
}


def _read_text_safe(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _detect_npm_frameworks(root: Path) -> list[str]:
    pkg = root / "package.json"
    text = _read_text_safe(pkg)
    if text is None:
        return []
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return []
    deps: dict[str, str] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        section = data.get(key)
        if isinstance(section, dict):
            deps.update(section)
    frameworks: list[str] = []
    seen: set[str] = set()
    for dep_name in deps:
        fw = _NPM_FRAMEWORKS.get(dep_name.lower())
        if fw and fw not in seen:
            frameworks.append(fw)
            seen.add(fw)
    return frameworks


def _detect_pypi_frameworks(root: Path) -> list[str]:
    """Detect Python frameworks from pyproject.toml and requirements.txt."""
    frameworks: list[str] = []
    seen: set[str] = set()

    # pyproject.toml — look for dependencies in [project] or [tool.poetry.dependencies]
    pp = root / "pyproject.toml"
    text = _read_text_safe(pp)
    if text is not None:
        for line in text.splitlines():
            stripped = line.strip()
            # Match lines like: "fastapi>=0.100" or 'django == 4.2'
            match = re.match(r'^["\']?([a-zA-Z0-9_-]+)["\']?\s*[;>=<~!]', stripped)
            if not match:
                match = re.match(r'^["\']?([a-zA-Z0-9_-]+)["\']?$', stripped)
            if match:
                dep = match.group(1).lower().replace("-", "_")
                fw = _PYPI_FRAMEWORKS.get(dep)
                if fw and fw not in seen:
                    frameworks.append(fw)
                    seen.add(fw)

    # requirements.txt
    req = root / "requirements.txt"
    text = _read_text_safe(req)
    if text is not None:
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = re.match(r'^([a-zA-Z0-9_-]+)', stripped)
            if match:
                dep = match.group(1).lower().replace("-", "_")
                fw = _PYPI_FRAMEWORKS.get(dep)
                if fw and fw not in seen:
                    frameworks.append(fw)
                    seen.add(fw)

    return frameworks


def _detect_cargo_frameworks(root: Path) -> list[str]:
    cargo = root / "Cargo.toml"
    text = _read_text_safe(cargo)
    if text is None:
        return []
    frameworks: list[str] = []
    seen: set[str] = set()
    in_deps = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "[dependencies]":
            in_deps = True
            continue
        if stripped.startswith("[") and in_deps:
            in_deps = False
            continue
        if in_deps and "=" in stripped:
            dep_name = stripped.split("=")[0].strip().strip('"').strip("'").lower()
            fw = _CARGO_FRAMEWORKS.get(dep_name)
            if fw and fw not in seen:
                frameworks.append(fw)
                seen.add(fw)
    return frameworks


def _detect_go_frameworks(root: Path) -> list[str]:
    go_mod = root / "go.mod"
    text = _read_text_safe(go_mod)
    if text is None:
        return []
    frameworks: list[str] = []
    seen: set[str] = set()
    in_require = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("require ("):
            in_require = True
            continue
        if in_require and stripped == ")":
            in_require = False
            continue
        if in_require or stripped.startswith("require "):
            mod = stripped.removeprefix("require ").strip()
            for fw_key, fw_val in _GO_FRAMEWORKS.items():
                if fw_key in mod and fw_val not in seen:
                    frameworks.append(fw_val)
                    seen.add(fw_val)
    return frameworks


def _detect_gradle_frameworks(root: Path) -> list[str]:
    frameworks: list[str] = []
    seen: set[str] = set()
    for name in ("build.gradle", "build.gradle.kts"):
        gradle = root / name
        text = _read_text_safe(gradle)
        if text is None:
            continue
        for match in _GRADLE_FRAMEWORKS_RE.finditer(text):
            group = match.group(2) or ""
            fw = _GRADLE_LIB_MAP.get(group)
            if fw and fw not in seen:
                frameworks.append(fw)
                seen.add(fw)
    return frameworks


def _detect_frameworks(root: Path) -> list[str]:
    """Inspect dependency manifests and return framework names."""
    all_frameworks: list[str] = []

    if (root / "package.json").is_file():
        all_frameworks.extend(_detect_npm_frameworks(root))
    if (root / "pyproject.toml").is_file() or (root / "requirements.txt").is_file():
        all_frameworks.extend(_detect_pypi_frameworks(root))
    if (root / "Cargo.toml").is_file():
        all_frameworks.extend(_detect_cargo_frameworks(root))
    if (root / "go.mod").is_file():
        all_frameworks.extend(_detect_go_frameworks(root))
    if (root / "build.gradle").is_file() or (root / "build.gradle.kts").is_file():
        all_frameworks.extend(_detect_gradle_frameworks(root))

    return all_frameworks


def _pubspec_stack(pubspec: Path) -> str:
    try:
        content = pubspec.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "Dart"
    return "Flutter (Dart)" if "flutter:" in content else "Dart"


def _detect_stack(root: Path) -> list[str]:
    stack: list[str] = []

    def add(name: str) -> None:
        if name not in stack:
            stack.append(name)

    for marker, name in ROOT_MARKERS.items():
        if (root / marker).is_file():
            add(name)
    pubspec = root / "pubspec.yaml"
    if pubspec.is_file():
        add(_pubspec_stack(pubspec))
    for pattern, name in ROOT_GLOBS.items():
        if any(root.glob(pattern)):
            add(name)
    # Frameworks are appended after languages so the stack reads "language, then framework".
    for fw in _detect_frameworks(root):
        add(fw)
    return stack


def _has_source_files(root: Path) -> bool:
    """Walk at most MAX_DEPTH levels and stop at the first source file."""
    root_depth = len(root.parts)
    for current, dirs, files in os.walk(root):
        depth = len(Path(current).parts) - root_depth
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and depth < MAX_DEPTH]
        if any(Path(name).suffix.lower() in SOURCE_EXTENSIONS for name in files):
            return True
    return False


def scan_project(project_root: str) -> ScanResult:
    """Inspect ``project_root`` and report whether it holds code and which stack it uses."""
    root = Path(project_root).resolve()
    stack = _detect_stack(root)
    return {"has_code": bool(stack) or _has_source_files(root), "detected_stack": stack}
