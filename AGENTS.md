# AGENTS.md

## Build & Run
- **Install**: `pip install -r requirements.txt && playwright install chromium`
- **Web**: `python run_web.py` (FastAPI + uvicorn on port 8000)
- **No tests**: This project has no test suite

## Environment
- Requires `GEMINI_API_KEY` env var for cover letter generation
- Requires `OPENAI_API_KEY` env var for text humanization (uses GPT-5.1)
- Uses virtual environment: `python3 -m venv venv && source venv/bin/activate`

## Third-Party Imports
- **Verify before using**: Before adding imports from third-party packages, verify they exist in the installed version:
  ```bash
  python -c "from package import SomeClass"
  ```
- **Check package version**: Run `pip show <package>` to see the installed version
- **Beware of API changes**: Packages evolve; imports may move between modules or packages (e.g., `Markup` moved from `jinja2` to `markupsafe` in Jinja2 3.0+)

## Code Style
- **Imports**: stdlib → third-party → local (`from app.config import ...`), separated by blank lines
- **Types**: Use type hints (`Optional`, `Generator`, `AsyncGenerator`), dataclasses for structured data
- **Naming**: snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants
- **Docstrings**: Module-level `"""Description."""`, Google-style for functions with Args/Returns/Raises
- **Error handling**: Wrap in try/except, log with `logger.error(f"...")`, re-raise or return error result
- **Paths**: Use `pathlib.Path`, not string paths; define path constants in `config.py`
- **Constants**: Define in `config.py` with descriptive comments (e.g., `MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB`)
- **Async**: Use `asyncio.to_thread()` to wrap sync functions; prefer native async when available
- **Private functions**: Prefix with underscore (e.g., `_extract_title`, `_load_static_prompt`)
