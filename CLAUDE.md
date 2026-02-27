# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenCrawler is a modular web content extraction tool that converts web pages to Markdown format. It uses a plugin-based architecture with FastAPI for REST API endpoints and Playwright for browser automation.

## Key Commands

### Development Setup
```bash
# Create virtual environment (using micromamba as shown in README)
micromamba create -p ./venv python=3.11.4
micromamba run -p ./venv pip install -r requirements.txt

# Install Playwright browsers
micromamba run -p ./venv playwright install chromium

# Setup environment
cp .env.example .env
# Edit .env file to configure cookies and settings
```

### Running the Application
```bash
# Start the FastAPI server
micromamba run -p ./venv python main.py

# Or using uvicorn directly
micromamba run -p ./venv uvicorn main:app --host 127.0.0.1 --port 8000

# API documentation available at:
# - Swagger UI: http://127.0.0.1:8000/docs
# - ReDoc: http://127.0.0.1:8000/redoc
```

### Testing
```bash
# Run tests (when test files are added)
python -m pytest test/

# Run specific test file
python -m pytest test/test_specific.py
```

## Architecture Overview

### Core Structure
- **API Layer** (`app/api/`): FastAPI endpoints for pages and articles
- **Plugin System** (`app/plugins/`): Platform-specific crawlers (GitHub, Zhihu, Xiaohongshu, WeChat, SSPAI, Generic)
- **Core Modules** (`app/core/`): Configuration, exceptions, and dependencies
- **Crawlers** (`app/crawlers/`): Base crawler classes and image downloader
- **Converters** (`app/converters/`): HTML to Markdown conversion and image extraction
- **Utils** (`app/utils/`): URL detection, file operations, and text processing

### Key Design Patterns

1. **Plugin Architecture**: Each platform is implemented as a plugin inheriting from `BasePlugin`
2. **Factory Pattern**: `CrawlerFactory` creates appropriate crawlers based on URL detection
3. **Dependency Injection**: FastAPI dependencies for browser sessions and configurations
4. **Exception Handling**: Custom `CrawlerException` with structured error responses

### Main API Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/pages/title?url=<URL>` - Extract page title
- `POST /api/v1/pages/extract` - Extract page content as JSON
- `POST /api/v1/articles` - Extract and save as Markdown file

### Plugin Development

To add a new platform:
1. Create plugin directory in `app/plugins/new_platform/`
2. Implement `NewPlatformCrawler` (inherits from `BaseCrawler`)
3. Implement `NewPlatformPlugin` (inherits from `BasePlugin`)
4. Add URL detection logic in `app/utils/url.py`
5. Add platform configuration in `app/core/config.py` if needed

### Configuration

Environment variables are managed through `.env` file:
- `HOST`, `PORT` - Server configuration
- `OUTPUT_DIR` - Where extracted content is saved
- `ZHIHU_COOKIE`, `XHS_COOKIE` - Platform authentication
- `PROXY_URL` - Optional proxy configuration
- `BROWSER_HEADLESS` - Browser mode

### File Structure Navigation

Key files for common tasks:
- **Adding new API endpoint**: `app/api/router.py` + new endpoint file
- **Adding new platform**: `app/plugins/` directory
- **Modifying extraction logic**: `app/crawlers/base.py` and platform-specific crawlers
- **Changing output format**: `app/converters/markdown.py`
- **Configuration changes**: `app/core/config.py`

### Error Handling

The application uses structured error handling:
- `CrawlerException` for crawler-specific errors
- FastAPI exception handlers for consistent API responses
- Logging throughout the application for debugging

### Testing Strategy

Test directory structure follows the main app structure:
- Unit tests for individual components
- Integration tests for API endpoints
- Plugin tests for platform-specific functionality

## Common Development Tasks

1. **Adding a new platform plugin**: Follow the pattern in existing plugins (github, zhihu, etc.)
2. **Modifying extraction behavior**: Update platform-specific crawler or base crawler
3. **API changes**: Update endpoint in `app/api/` and ensure proper request/response models
4. **Configuration updates**: Add new settings in `app/core/config.py`
5. **Image handling**: Modify `app/crawlers/image_downloader.py` or `app/converters/image_extractor.py`