from fastapi import FastAPI
from app.routers import properties, leads
from app.routers import dashboard
from app.routers import whatsapp

app = FastAPI(title="Real Estate Platform API")

app.include_router(properties.router)
app.include_router(leads.router)
app.include_router(whatsapp.router)
app.include_router(dashboard.router)

@app.get("/")
def root():
    return {"message": "API running"}

# uvicorn app.main:app --reload