from procrastinate import App, PsycopgConnector

RUN_ANALYSIS = "run_analysis"
ANALYSIS_QUEUE = "analysis"


def job_dsn(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


def create_job_app(database_url: str, import_paths: list[str] | None = None) -> App:
    return App(
        connector=PsycopgConnector(conninfo=job_dsn(database_url)),
        import_paths=import_paths or [],
    )
