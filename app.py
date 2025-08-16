# app.py
from fastapi import FastAPI
from routes import auth_routes, session_routes, bill_routes, payment_routes, split_routes  # import other routes later
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ZeroTabs Backend", version="1.0.0")

# Allow frontend origin(s)
origins = [
    "http://localhost:8080",  # Vite dev server
    "http://localhost:3000",  # CRA dev server
    "https://your-frontend-domain.com"  # Production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # or ["*"] for all origins
    allow_credentials=True,
    allow_methods=["*"],            # ["GET", "POST"] if you want to restrict
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(session_routes.router)
app.include_router(bill_routes.router)
app.include_router(payment_routes.router)
app.include_router(split_routes.router)

# Root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to ZeroTabs API 🚀"}
