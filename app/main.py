from fastapi import FastAPI
from app.routers import properties, leads, dashboard, whatsapp, idecor, tasaciones
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Real Estate Platform API")

origins = [
    "http://localhost:5173",
    "https://frontend-plataforma-inmobiliaria.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(properties.router)
app.include_router(leads.router)
app.include_router(whatsapp.router)
app.include_router(dashboard.router)
app.include_router(idecor.router)
app.include_router(tasaciones.router)

@app.get("/")
def root():
    return {"message": "API running"}

# uvicorn app.main:app --reload