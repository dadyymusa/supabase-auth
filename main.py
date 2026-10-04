import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client

security = HTTPBearer(auto_error=False)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

PORT = int(os.getenv("PORT", 3000))

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server running and connected to Supabase")
    yield

app = FastAPI(lifespan=lifespan)

class SignUp(BaseModel):
    email: EmailStr
    password: str

class LogIn(BaseModel):
    email: EmailStr
    password: str

@app.post("/auth/signup")
def signup(body: SignUp):
    try:
        response = supabase.auth.sign_up({
            "email": body.email,
            "password": body.password
        })

        if not response.user:
            return JSONResponse(status_code=400, content={"detail": "User object is missing in response"})

        return JSONResponse(status_code=201, content={"user": response.user.model_dump()})
    
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})

@app.post("/auth/login")
async def login(body: LogIn):
    try:
        response = supabase.auth.sign_in_with_password({
            "email" : body.email,
            "password" : body.password
        })

        if not response.user or not response.session:
            return JSONResponse(status_code= 400, content= {"detail" : "Bad Request"})
        
        return JSONResponse(status_code= 200, content= {
            "access_token" : response.session.access_token,
            "refresh_token" : response.session.refresh_token, 
            "token_type" : "bearer", 
            "user" : {
                "id" : response.user.id, 
                "email" : response.user.email
            }
        }) 
    except Exception:
        return JSONResponse(status_code= 400, content= {"detail" : "Bad Request"})

@app.get("/public/info")
async def public():
    return JSONResponse(status_code= 200, content= {"message" : "Welcome Stranger! This info is public"})

@app.get("/protected/profile")
async def profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials or not credentials.credentials:
        return JSONResponse(status_code=401, content={"error": "Access token required"})

    token = credentials.credentials

    try:
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            return JSONResponse(status_code=401, content={"error": "Access token required"})

        return {
            "message": "Welcome to your protected profile!",
            "user_id": user_response.user.id,
            "email": user_response.user.email,
            "created_at": user_response.user.created_at
        }
    except Exception:
        return JSONResponse(status_code=401, content={"error": "Access token required"})
