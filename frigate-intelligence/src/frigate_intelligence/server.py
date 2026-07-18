import uvicorn

from frigate_intelligence.config.settings import Settings
from frigate_intelligence.config.dependencies import create_container
from frigate_intelligence.infrastructure.api.fastapi_app import create_app


def main():
    settings = Settings()
    container = create_container(settings)
    app = create_app(container)
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
