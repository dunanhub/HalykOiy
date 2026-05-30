from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.flights import router as flights_router
from app.routers.hotels import router as hotels_router
from app.routers.transfer import router as transfer_router
from app.routers.activities import router as activities_router
from app.routers.pharmacy import router as pharmacy_router
from app.routers.pay import router as pay_router
from app.routers.restaurants import router as restaurants_router
from app.routers.insurance import router as insurance_router
from app.routers.travel import router as travel_router

app = FastAPI(title="Halyk Travel AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(flights_router)
app.include_router(hotels_router)
app.include_router(transfer_router)
app.include_router(activities_router)
app.include_router(pharmacy_router)
app.include_router(pay_router)
app.include_router(restaurants_router)
app.include_router(insurance_router)
app.include_router(travel_router)

@app.get("/")
async def root():
    return {"status": "ok"}
