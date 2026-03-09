from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.auth import router as auth_router
from app.api.projects import router as projects_router
from app.api.links import router as links_router

app = FastAPI(title="URL Shortener API", version="1.0.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(links_router)