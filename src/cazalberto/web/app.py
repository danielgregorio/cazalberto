"""
Aplicação FastAPI - Painel de controle web do Cazalberto
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..core.config import settings
from ..core.logging import get_logger
from .api import router as api_router

logger = get_logger("web")

# Criar aplicação FastAPI
app = FastAPI(
    title="Cazalberto Control Panel",
    description="Painel de controle para gerenciar o bot Cazalberto",
    version=settings.bot_version,
)

# Templates Jinja2
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Static files (CSS, JS, imagens)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Incluir rotas da API
app.include_router(api_router, prefix="/api", tags=["api"])


@app.on_event("startup")
async def startup_event() -> None:
    """Executa ao iniciar a aplicação"""
    logger.info(f"Painel web iniciando na porta {settings.web_port}...")
    logger.info(f"Acesse: http://{settings.web_host}:{settings.web_port}")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Executa ao desligar a aplicação"""
    logger.info("Painel web desligando...")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """Página inicial do painel"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Dashboard - Cazalberto",
            "version": settings.bot_version,
        },
    )


@app.get("/audios", response_class=HTMLResponse)
async def audios_page(request: Request) -> HTMLResponse:
    """Página de gerenciamento de áudios"""
    return templates.TemplateResponse(
        "audios.html",
        {
            "request": request,
            "title": "Gerenciar Áudios - Cazalberto",
        },
    )


@app.get("/playlists", response_class=HTMLResponse)
async def playlists_page(request: Request) -> HTMLResponse:
    """Página de gerenciamento de playlists"""
    return templates.TemplateResponse(
        "playlists.html",
        {
            "request": request,
            "title": "Gerenciar Playlists - Cazalberto",
        },
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.bot_version}


def main() -> None:
    """Inicia o servidor web"""
    import uvicorn

    uvicorn.run(
        "cazalberto.web.app:app",
        host=settings.web_host,
        port=settings.web_port,
        reload=settings.web_reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
