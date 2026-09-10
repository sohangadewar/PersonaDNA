import os
import base64
import re
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / "backend" / ".env"

load_dotenv(ENV_FILE)

GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


# ============================================================
# GitHub Username
# ============================================================


def extract_github_username(github_url: str) -> str:
    if not github_url:
        return ""

    github_url = str(github_url).strip().strip("`").strip()

    if not github_url.startswith(("http://", "https://")):
        github_url = "https://" + github_url

    parsed = urlparse(github_url)

    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        return ""

    path = parsed.path.strip("/")

    if not path:
        return ""

    username = path.split("/")[0].strip().strip("`").strip()

    return username


# ============================================================
# GitHub API Helper
# ============================================================


def github_get(url: str, params: dict | None = None):
    try:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "PersonaDNA",
        }

        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

        response = requests.get(url, params=params, timeout=10, headers=headers)

        print("GitHub URL:", response.url)
        print("GitHub Status:", response.status_code)

        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining")
            reset = response.headers.get("X-RateLimit-Reset")
            print(f"GitHub rate limit. Remaining={remaining}, Reset={reset}")
            return None

        if response.status_code == 404:
            print("GitHub resource not found:", url)
            return None

        if response.status_code != 200:
            print("GitHub Error:", response.text[:500])
            return None

        return response.json()

    except requests.RequestException as e:
        print("GitHub Request Error:", str(e))
        return None


# ============================================================
# Get File Content
# ============================================================


def get_file_content(owner: str, repo_name: str, file_path: str) -> str:
    """
    Download and decode a text file from a GitHub repository.
    """
    url = f"{GITHUB_API}/repos/{owner}/{repo_name}/contents/{file_path}"

    data = github_get(url)

    if not data:
        return ""

    encoded_content = data.get("content")

    if not encoded_content:
        return ""

    try:
        return base64.b64decode(encoded_content).decode("utf-8", errors="ignore")
    except Exception:
        return ""


# ============================================================
# Dependency Detection
# ============================================================


def detect_dependencies(owner: str, repo_name: str, files: list[str]) -> dict:
    """
    Inspect common dependency/configuration files and identify technologies actually used.
    """
    technologies = []
    dependency_files = {}

    normalized_files = {file.lower(): file for file in files}

    # --- requirements.txt ---
    requirements_file = normalized_files.get("requirements.txt")
    if requirements_file:
        content = get_file_content(owner, repo_name, requirements_file)
        dependency_files["requirements.txt"] = bool(content)
        content_lower = content.lower()

        python_dependencies = {
            "FastAPI": "fastapi",
            "Flask": "flask",
            "Django": "django",
            "SQLAlchemy": "sqlalchemy",
            "OpenCV": "opencv",
            "Pandas": "pandas",
            "NumPy": "numpy",
            "PyTorch": "torch",
            "TensorFlow": "tensorflow",
            "Scikit-learn": "scikit-learn",
            "Requests": "requests",
            "Pygame": "pygame",
        }
        for technology, package in python_dependencies.items():
            if package in content_lower:
                technologies.append(technology)

    # --- package.json ---
    package_file = normalized_files.get("package.json")
    if package_file:
        content = get_file_content(owner, repo_name, package_file)
        dependency_files["package.json"] = bool(content)
        content_lower = content.lower()

        javascript_dependencies = {
            "React": '"react"',
            "React Router": '"react-router',
            "Redux": '"redux"',
            "Express.js": '"express"',
            "Axios": '"axios"',
            "Vite": '"vite"',
            "Next.js": '"next"',
            "Tailwind CSS": '"tailwindcss"',
        }
        for technology, package in javascript_dependencies.items():
            if package in content_lower:
                technologies.append(technology)

    # --- Dockerfile ---
    dockerfile = normalized_files.get("dockerfile")
    if dockerfile:
        dependency_files["Dockerfile"] = True
        technologies.append("Docker")

    # --- pyproject.toml ---
    pyproject = normalized_files.get("pyproject.toml")
    if pyproject:
        content = get_file_content(owner, repo_name, pyproject)
        dependency_files["pyproject.toml"] = bool(content)
        content_lower = content.lower()

        pyproject_dependencies = {
            "FastAPI": "fastapi",
            "Flask": "flask",
            "Django": "django",
            "Pandas": "pandas",
            "NumPy": "numpy",
            "SQLAlchemy": "sqlalchemy",
        }
        for technology, package in pyproject_dependencies.items():
            if package in content_lower:
                technologies.append(technology)

    return {
        "technologies": list(dict.fromkeys(technologies)),
        "dependency_files": dependency_files,
    }




# ============================================================
# RAG + Jarvis Evidence Detection
# ============================================================


def detect_rag_and_jarvis_evidence(
    owner: str, repo_name: str, files: list[str]
) -> dict:
    """
    Detect actual RAG and Jarvis evidence from repository files.
    This is evidence-based detection, not resume-based guessing.
    """
    technologies = []
    evidence = {"rag": [], "jarvis": []}
    normalized_files = {file.lower(): file for file in files}

    rag_file_patterns = [
        "rag",
        "retrieval",
        "retriever",
        "vector",
        "embedding",
        "embeddings",
        "chromadb",
        "faiss",
        "qdrant",
        "pinecone",
        "pgvector",
        "langchain",
        "llamaindex",
    ]
    jarvis_file_patterns = [
        "jarvis",
        "assistant",
        "voice",
        "speech",
        "tts",
        "stt",
        "speech_recognition",
        "pyttsx3",
        "pygame",
        "wake_word",
        "wakeword",
    ]

    for original_file in files:
        file_lower = original_file.lower()

        for pattern in rag_file_patterns:
            if pattern in file_lower:
                evidence["rag"].append({"file": original_file, "indicator": pattern})
                if "RAG" not in technologies:
                    technologies.append("RAG")
                break

        for pattern in jarvis_file_patterns:
            if pattern in file_lower:
                evidence["jarvis"].append({"file": original_file, "indicator": pattern})
                if "Jarvis" not in technologies:
                    technologies.append("Jarvis")
                break

    dependency_files_to_check = ["requirements.txt", "pyproject.toml", "package.json"]

    for dependency_file in dependency_files_to_check:
        actual_file = normalized_files.get(dependency_file)
        if not actual_file:
            continue

        content = get_file_content(owner, repo_name, actual_file)
        if not content:
            continue

        content_lower = content.lower()

        rag_dependencies = [
            "langchain",
            "langchain-community",
            "langchain-core",
            "langchain-openai",
            "langchain-google",
            "llama-index",
            "chromadb",
            "faiss",
            "qdrant",
            "pinecone",
            "pgvector",
            "sentence-transformers",
        ]
        for dependency in rag_dependencies:
            if dependency in content_lower:
                evidence["rag"].append({"file": actual_file, "dependency": dependency})
                if "RAG" not in technologies:
                    technologies.append("RAG")

        jarvis_dependencies = [
            "speechrecognition",
            "pyttsx3",
            "pygame",
            "pyaudio",
            "vosk",
            "openai",
            "google-generativeai",
        ]
        for dependency in jarvis_dependencies:
            if dependency in content_lower:
                evidence["jarvis"].append(
                    {"file": actual_file, "dependency": dependency}
                )
                if "Jarvis" not in technologies:
                    technologies.append("Jarvis")

    return {"technologies": technologies, "evidence": evidence}

# ============================================================
# Main GitHub Analyzer
# ============================================================

# ============================================================
# Main GitHub Analyzer
# ============================================================

def analyze_github(github_url: str) -> dict:
    """
    Analyze a public GitHub profile and collect
    repository-level technology evidence.
    """

    username = extract_github_username(github_url)

    # --------------------------------------------------------
    # Missing / invalid URL
    # --------------------------------------------------------

    if not username:
        return {
            "username": "",
            "profile_found": False,
            "repository_count": 0,
            "repositories": [],
            "technology_evidence": [],
            "evidence_status": "missing",
        }

    # --------------------------------------------------------
    # GitHub Profile
    # --------------------------------------------------------

    profile = github_get(
        f"{GITHUB_API}/users/{username}"
    )

    if not profile:
        return {
            "username": username,
            "profile_found": False,
            "repository_count": 0,
            "repositories": [],
            "technology_evidence": [],
            "evidence_status": "not_found",
        }

    # --------------------------------------------------------
    # Repositories
    # --------------------------------------------------------

    repositories = github_get(
        f"{GITHUB_API}/users/{username}/repos",
        params={
            "per_page": 10,
            "sort": "updated",
        },
    )

    if not isinstance(repositories, list):
        return {
            "username": username,
            "profile_found": True,
            "display_name": profile.get("name"),
            "bio": profile.get("bio"),
            "public_repositories": profile.get(
                "public_repos",
                0,
            ),
            "repository_count": 0,
            "repositories": [],
            "technology_evidence": [],
            "evidence_status": "repository_api_error",
        }

    # --------------------------------------------------------
    # Analyze Repositories
    # --------------------------------------------------------

    analyzed_repositories = []

    for repository in repositories:

        if not isinstance(repository, dict):
            continue

        analyzed_repository = analyze_repository(
            username,
            repository,
        )

        analyzed_repositories.append(
            analyzed_repository
        )

    # --------------------------------------------------------
    # Technology Evidence
    # --------------------------------------------------------

    technology_evidence = []

    for repository in analyzed_repositories:

        repository_technologies = repository.get(
            "technologies",
            [],
        )

        if not isinstance(
            repository_technologies,
            list,
        ):
            continue

        technology_evidence.extend(
            repository_technologies
        )

    technology_evidence = list(
        dict.fromkeys(
            technology_evidence
        )
    )

    # --------------------------------------------------------
    # Final GitHub Evidence
    # --------------------------------------------------------

    return {
        "username": username,
        "profile_found": True,
        "display_name": profile.get("name"),
        "bio": profile.get("bio"),
        "public_repositories": profile.get(
            "public_repos",
            0,
        ),
        "repository_count": len(
            analyzed_repositories
        ),
        "repositories": analyzed_repositories,
        "technology_evidence": technology_evidence,
        "evidence_status": (
            "found"
            if analyzed_repositories
            else "no_repositories"
        ),
    }

# ============================================================
# Repository Analysis
# ============================================================


# ============================================================
# Repository Analysis
# ============================================================


def analyze_repository(
    username: str,
    repository: dict,
) -> dict:
    """
    Analyze one GitHub repository.

    Uses the Git Trees API to collect repository files
    recursively in a single API request instead of making
    one request for every directory.
    """

    repo_name = repository.get("name", "")

    owner = repository.get(
        "owner",
        {},
    ).get(
        "login",
        username,
    )

    language = repository.get("language")
    description = repository.get("description")

    stars = repository.get(
        "stargazers_count",
        0,
    )

    forks = repository.get(
        "forks_count",
        0,
    )

    updated_at = repository.get("updated_at")

    # --------------------------------------------------------
    # Languages
    # --------------------------------------------------------

    languages_url = repository.get("languages_url")

    languages = {}

    if languages_url:

        language_data = github_get(languages_url)

        if isinstance(
            language_data,
            dict,
        ):
            languages = language_data

    # --------------------------------------------------------
    # Repository Files
    #
    # Git Trees API gives us the complete repository tree
    # recursively in one request.
    # --------------------------------------------------------

    files = []

    default_branch = repository.get("default_branch")

    if default_branch:

        tree_url = (
            f"{GITHUB_API}/repos/" f"{owner}/{repo_name}/git/trees/" f"{default_branch}"
        )

        tree_data = github_get(
            tree_url,
            params={
                "recursive": "1",
            },
        )

        if isinstance(
            tree_data,
            dict,
        ):

            tree_items = tree_data.get(
                "tree",
                [],
            )

            if isinstance(
                tree_items,
                list,
            ):

                for item in tree_items:

                    if not isinstance(
                        item,
                        dict,
                    ):
                        continue

                    if item.get("type") != "blob":
                        continue

                    path = item.get(
                        "path",
                        "",
                    )

                    if path:
                        files.append(path)

            if tree_data.get("truncated"):

                print(f"GitHub tree truncated: " f"{owner}/{repo_name}")

    # --------------------------------------------------------
    # README
    #
    # We don't need another API request just to determine
    # whether README exists.
    # --------------------------------------------------------

    has_readme = any(
        file.lower()
        in {
            "readme",
            "readme.md",
            "readme.txt",
            "readme.rst",
        }
        or file.lower().startswith("readme.")
        for file in files
    )

    # --------------------------------------------------------
    # Basic Technology Detection
    # --------------------------------------------------------

    searchable_text = " ".join(
        [
            repo_name,
            description or "",
            language or "",
            " ".join(languages.keys()),
            " ".join(files),
        ]
    ).lower()

    technologies = []

    technology_patterns = {
        "Python": [
            "python",
            ".py",
        ],
        "JavaScript": [
            "javascript",
            ".js",
        ],
        "TypeScript": [
            "typescript",
            ".ts",
        ],
        "React": [
            "react",
            ".jsx",
            ".tsx",
        ],
        "Node.js": [
            "node",
        ],
        "SQL": [
            "sql",
            "mysql",
            "postgresql",
            "sqlite",
        ],
        "MongoDB": [
            "mongodb",
            "mongoose",
        ],
        "AI": [
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "ai",
        ],
    }

    for technology, patterns in technology_patterns.items():

        for pattern in patterns:

            pattern_lower = pattern.lower()

            # Longer phrases / extensions can use
            # normal substring matching.
            if (
                pattern_lower.startswith(".")
                or " " in pattern_lower
                or len(pattern_lower) > 4
            ):

                matched = pattern_lower in searchable_text

            else:

                # Prevent false matches such as:
                # "ai" inside "maintain"
                # "sql" inside unrelated words
                matched = (
                    re.search(
                        r"\b" + re.escape(pattern_lower) + r"\b",
                        searchable_text,
                    )
                    is not None
                )

            if matched:

                technologies.append(technology)

                break

    # --------------------------------------------------------
    # Dependency Detection
    # --------------------------------------------------------

    dependency_result = detect_dependencies(
        owner,
        repo_name,
        files,
    )

    technologies.extend(
        dependency_result.get(
            "technologies",
            [],
        )
    )

    technologies = list(dict.fromkeys(technologies))

    # --------------------------------------------------------
    # RAG / Jarvis Evidence
    # --------------------------------------------------------

    specialized_evidence = detect_rag_and_jarvis_evidence(
        owner,
        repo_name,
        files,
    )

    technologies.extend(
        specialized_evidence.get(
            "technologies",
            [],
        )
    )

    technologies = list(dict.fromkeys(technologies))

    # --------------------------------------------------------
    # Return Repository Evidence
    # --------------------------------------------------------

    return {
        "name": repo_name,
        "description": description,
        "language": language,
        "languages": languages,
        "technologies": technologies,
        "dependency_files": (
            dependency_result.get(
                "dependency_files",
                {},
            )
        ),
        "specialized_evidence": (
            specialized_evidence.get(
                "evidence",
                {},
            )
        ),
        "files": files,
        "has_readme": has_readme,
        "stars": stars,
        "forks": forks,
        "updated_at": updated_at,
    }
