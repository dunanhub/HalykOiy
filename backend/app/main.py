from fastapi import FastAPI, WebSocket
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
from workflow import run_workflow

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


@app.websocket("/ws/travel")
async def travel_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        user_text = data.get("text", "")
        if not user_text.strip():
            await websocket.send_json({"type": "error", "text": "Укажи куда хочешь поехать"})
            return
        await run_workflow(user_text, stream=websocket, partial_request=data.get("partial_request"))
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "text": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
