# final_project/web.py
from fastapi import FastAPI, HTTPException, Depends
from .cli import build_services
from pydantic import BaseModel

app = FastAPI(title="final_project API")

class RegisterIn(BaseModel):
    username: str
    password: str
    email: str | None = None

def get_services():
    return build_services()

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/register")
def register(payload: RegisterIn, services=Depends(get_services)):
    acc_svc, _ = services
    try:
        acc = acc_svc.register(payload.username, payload.password, payload.email)
        return {"username": acc.username, "created": acc.created}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
