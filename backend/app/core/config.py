from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "ChessMotion"
    APP_ENV: str = "development"

    TEMP_DIR: Path = Path("./temp")
    OUTPUT_DIR: Path = Path("./output")
    ASSETS_DIR: Path = Path("./assets")

    # Stored as comma-separated string in .env: "http://localhost:3000,http://localhost:3001"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    STOCKFISH_PATH: str = ""
    LICHESS_TOKEN: str = ""

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    def model_post_init(self, __context):
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
