from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# JWT settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 72

# LLM setup
LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# FastAPI app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Auth helpers
def create_access_token(user_id: str, user_type: str):
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode = {"sub": user_id, "user_type": user_type, "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    user_type: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    reset_code: str
    new_password: str

class PatientProfileCreate(BaseModel):
    raw_input: str
    location: Optional[str] = None

class ResearcherProfileCreate(BaseModel):
    specialties: List[str]
    research_interests: List[str]
    orcid: Optional[str] = None
    researchgate: Optional[str] = None
    availability: bool = False
    bio: Optional[str] = None

class ClinicalTrialCreate(BaseModel):
    title: str
    description: str
    phase: str
    status: str
    location: str
    eligibility: str
    contact: str
    conditions: List[str]

class ForumCreate(BaseModel):
    category: str
    title: str
    description: str

class ForumPostCreate(BaseModel):
    forum_id: str
    content: str
    parent_id: Optional[str] = None

class MessageCreate(BaseModel):
    to_user: str
    message: str

class FavoriteCreate(BaseModel):
    item_type: str
    item_id: str

class ConnectionRequestCreate(BaseModel):
    to_user: str

class MeetingRequestCreate(BaseModel):
    expert_id: str
    notes: Optional[str] = None

# API endpoints
@api_router.post("/auth/register")
async def register(user_data: UserRegister):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = pwd_context.hash(user_data.password)
    new_user = {
        "id": str(uuid.uuid4()),
        "email": user_data.email,
        "password_hash": hashed_password,
        "user_type": user_data.user_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(new_user)
    
    token = create_access_token(new_user["id"], new_user["user_type"])
    return {"token": token, "user_id": new_user["id"], "user_type": new_user["user_type"]}

@api_router.post("/auth/login")
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email})
    if not user or not pwd_context.verify(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(user["id"], user["user_type"])
    return {"token": token, "user_id": user["id"], "user_type": user["user_type"]}

@api_router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    user = await db.users.find_one({"email": request.email})
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a reset code has been sent"}
    
    # Generate 6-digit reset code
    reset_code = str(uuid.uuid4().int)[:6]
    
    # Store reset code with expiration (15 minutes)
    await db.password_resets.insert_one({
        "email": request.email,
        "reset_code": reset_code,
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # In production, send email here. For MVP, return code (remove in production!)
    return {"message": "Reset code sent to email", "reset_code": reset_code}

@api_router.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    # Find valid reset code
    reset_doc = await db.password_resets.find_one({
        "email": request.email,
        "reset_code": request.reset_code
    })
    
    if not reset_doc:
        raise HTTPException(status_code=400, detail="Invalid reset code")
    
    # Check if expired
    if datetime.fromisoformat(reset_doc["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset code expired")
    
    # Update password
    hashed_password = pwd_context.hash(request.new_password)
    await db.users.update_one(
        {"email": request.email},
        {"$set": {"password_hash": hashed_password}}
    )
    
    # Delete used reset code
    await db.password_resets.delete_one({"_id": reset_doc["_id"]})
    
    return {"message": "Password reset successfully"}

@api_router.get("/auth/me")
async def get_me(payload: dict = Depends(verify_token)):
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user["id"], "email": user["email"], "user_type": user["user_type"]}

@api_router.post("/patients/profile")
async def create_patient_profile(profile: PatientProfileCreate, payload: dict = Depends(verify_token)):
    user_id = payload["sub"]
    
    # Use AI to extract conditions
    try:
        chat = LlmChat(api_key=LLM_KEY, session_id=f"patient_{user_id}", system_message="You are a medical condition identifier. Extract medical conditions from user input and return as JSON array.")
        chat.with_model("openai", "gpt-5")
        message = UserMessage(text=f"Extract medical conditions from: {profile.raw_input}. Return ONLY a JSON array of conditions, nothing else.")
        response = await chat.send_message(message)
        
        import json
        try:
            conditions = json.loads(response)
        except:
            conditions = [profile.raw_input]
    except Exception as e:
        conditions = [profile.raw_input]
    
    existing = await db.patient_profiles.find_one({"user_id": user_id})
    if existing:
        await db.patient_profiles.update_one(
            {"user_id": user_id},
            {"$set": {
                "conditions": conditions,
                "location": profile.location,
                "raw_input": profile.raw_input
            }}
        )
        return {"id": existing["id"], "conditions": conditions}
    
    new_profile = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "conditions": conditions,
        "location": profile.location,
        "raw_input": profile.raw_input,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.patient_profiles.insert_one(new_profile)
    return {"id": new_profile["id"], "conditions": conditions}

@api_router.get("/patients/dashboard")
async def get_patient_dashboard(payload: dict = Depends(verify_token)):
    user_id = payload["sub"]
    profile = await db.patient_profiles.find_one({"user_id": user_id}, {"_id": 0})
    
    trials = await db.clinical_trials.find({}, {"_id": 0}).limit(5).to_list(5)
    publications = await db.publications.find({}, {"_id": 0}).limit(5).to_list(5)
    experts = await db.health_experts.find({}, {"_id": 0}).limit(5).to_list(5)
    
    return {
        "profile": profile,
        "trials": trials,
        "publications": publications,
        "experts": experts
    }

@api_router.get("/patients/experts")
async def get_health_experts():
    experts = await db.health_experts.find({}, {"_id": 0}).limit(20).to_list(20)
    return experts

@api_router.get("/patients/clinical-trials")
async def search_clinical_trials(query: Optional[str] = None, status: Optional[str] = None):
    filter_query = {}
    if status:
        filter_query["status"] = status
    trials = await db.clinical_trials.find(filter_query, {"_id": 0}).limit(20).to_list(20)
    return trials

@api_router.get("/patients/publications")
async def search_publications():
    publications = await db.publications.find({}, {"_id": 0}).limit(20).to_list(20)
    return publications

@api_router.post("/researchers/profile")
async def create_researcher_profile(profile: ResearcherProfileCreate, payload: dict = Depends(verify_token)):
    user_id = payload["sub"]
    
    existing = await db.researcher_profiles.find_one({"user_id": user_id})
    profile_data = {
        "specialties": profile.specialties,
        "research_interests": profile.research_interests,
        "orcid": profile.orcid,
        "researchgate": profile.researchgate,
        "availability": profile.availability,
        "bio": profile.bio
    }
    
    if existing:
        await db.researcher_profiles.update_one({"user_id": user_id}, {"$set": profile_data})
        profile_id = existing["id"]
    else:
        profile_data.update({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        await db.researcher_profiles.insert_one(profile_data)
        profile_id = profile_data["id"]
        
        # Create health expert entry
        user = await db.users.find_one({"id": user_id})
        expert = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": user["email"].split('@')[0],
            "specialty": profile.specialties,
            "research_interests": profile.research_interests,
            "is_registered": True,
            "bio": profile.bio,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.health_experts.insert_one(expert)
    
    return {"id": profile_id}

@api_router.get("/researchers/dashboard")
async def get_researcher_dashboard(payload: dict = Depends(verify_token)):
    user_id = payload["sub"]
    profile = await db.researcher_profiles.find_one({"user_id": user_id}, {"_id": 0})
    
    trials = await db.clinical_trials.find({"created_by": user_id}, {"_id": 0}).to_list(100)
    forums = await db.forums.find({"created_by": user_id}, {"_id": 0}).to_list(100)
    
    return {
        "profile": profile or {},
        "trials": trials,
        "forums": forums
    }

@api_router.get("/researchers/collaborators")
async def get_collaborators():
    researchers = await db.users.find({"user_type": "researcher"}, {"_id": 0}).limit(20).to_list(20)
    result = []
    for r in researchers:
        profile = await db.researcher_profiles.find_one({"user_id": r["id"]}, {"_id": 0})
        if profile:
            result.append({
                "id": r["id"],
                "name": r["email"].split('@')[0],
                "specialties": profile.get("specialties", []),
                "research_interests": profile.get("research_interests", [])
            })
    return result

@api_router.post("/researchers/clinical-trials")
async def create_clinical_trial(trial: ClinicalTrialCreate, payload: dict = Depends(verify_token)):
    user_id = payload["sub"]
    
    new_trial = {
        "id": str(uuid.uuid4()),
        "nct_id": f"NCT{uuid.uuid4().hex[:8].upper()}",
        "title": trial.title,
        "description": trial.description,
        "phase": trial.phase,
        "status": trial.status,
        "location": trial.location,
        "eligibility": trial.eligibility,
        "contact": trial.contact,
        "conditions": trial.conditions,
        "created_by": user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.clinical_trials.insert_one(new_trial)
    return {"id": new_trial["id"], "nct_id": new_trial["nct_id"]}

@api_router.put("/researchers/clinical-trials/{trial_id}")
async def update_clinical_trial(trial_id: str, trial: ClinicalTrialCreate, payload: dict = Depends(verify_token)):
    result = await db.clinical_trials.update_one(
        {"id": trial_id},
        {"$set": {
            "title": trial.title,
            "description": trial.description,
            "phase": trial.phase,
            "status": trial.status,
            "location": trial.location,
            "eligibility": trial.eligibility,
            "contact": trial.contact,
            "conditions": trial.conditions
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Trial not found")
    return {"id": trial_id}

@api_router.post("/connection-requests")
async def create_connection_request(request: ConnectionRequestCreate, payload: dict = Depends(verify_token)):
    from_user = payload["sub"]
    
    existing = await db.connection_requests.find_one({
        "from_user": from_user,
        "to_user": request.to_user
    })
    
    if existing:
        return {"id": existing["id"], "status": existing["status"]}
    
    new_request = {
        "id": str(uuid.uuid4()),
        "from_user": from_user,
        "to_user": request.to_user,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.connection_requests.insert_one(new_request)
    return {"id": new_request["id"], "status": new_request["status"]}

@api_router.get("/connection-requests")
async def get_connection_requests(payload: dict = Depends(verify_token)):
    user_id = payload["sub"]
    requests = await db.connection_requests.find({
        "$or": [{"from_user": user_id}, {"to_user": user_id}]
    }, {"_id": 0}).to_list(100)
    return requests

@api_router.post("/forums")
async def create_forum(forum: ForumCreate, payload: dict = Depends(verify_token)):
    user_id = payload["sub"]
    
    new_forum = {
        "id": str(uuid.uuid4()),
        "category": forum.category,
        "title": forum.title,
        "description": forum.description,
        "created_by": user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.forums.insert_one(new_forum)
    return {"id": new_forum["id"]}

@api_router.get("/forums")
async def get_forums(category: Optional[str] = None):
    filter_query = {"category": category} if category else {}
    forums = await db.forums.find(filter_query, {"_id": 0}).to_list(100)
    return forums

@api_router.post("/forums/posts")
async def create_forum_post(post: ForumPostCreate, payload: dict = Depends(verify_token)):
    user_id = payload["sub"]
    
    new_post = {
        "id": str(uuid.uuid4()),
        "forum_id": post.forum_id,
        "user_id": user_id,
        "content": post.content,
        "parent_id": post.parent_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.forum_posts.insert_one(new_post)
    return {"id": new_post["id"]}

@api_router.get("/forums/{forum_id}/posts")
async def get_forum_posts(forum_id: str):
    posts = await db.forum_posts.find({"forum_id": forum_id}, {"_id": 0}).to_list(100)
    return posts

@api_router.post("/chat/messages")
async def send_message(message: MessageCreate, payload: dict = Depends(verify_token)):
    from_user = payload["sub"]
    
    new_message = {
        "id": str(uuid.uuid4()),
        "from_user": from_user,
        "to_user": message.to_user,
        "message": message.message,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.messages.insert_one(new_message)
    return {"id": new_message["id"]}

@api_router.get("/chat/messages/{user_id}")
async def get_messages(user_id: str, payload: dict = Depends(verify_token)):
    current_user = payload["sub"]
    messages = await db.messages.find({
        "$or": [
            {"from_user": current_user, "to_user": user_id},
            {"from_user": user_id, "to_user": current_user}
        ]
    }, {"_id": 0}).sort("created_at", 1).to_list(1000)
    return messages

@api_router.post("/favorites")
async def add_favorite(favorite: FavoriteCreate, payload: dict = Depends(verify_token)):
    user_id = payload["sub"]
    
    existing = await db.favorites.find_one({
        "user_id": user_id,
        "item_type": favorite.item_type,
        "item_id": favorite.item_id
    })
    
    if existing:
        await db.favorites.delete_one({"id": existing["id"]})
        return {"removed": True}
    
    new_favorite = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "item_type": favorite.item_type,
        "item_id": favorite.item_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.favorites.insert_one(new_favorite)
    return {"id": new_favorite["id"], "added": True}

@api_router.get("/favorites")
async def get_favorites(payload: dict = Depends(verify_token)):
    user_id = payload["sub"]
    favorites = await db.favorites.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    result = {"trials": [], "publications": [], "experts": []}
    for f in favorites:
        if f["item_type"] == "trial":
            trial = await db.clinical_trials.find_one({"id": f["item_id"]}, {"_id": 0})
            if trial:
                result["trials"].append(trial)
        elif f["item_type"] == "publication":
            pub = await db.publications.find_one({"id": f["item_id"]}, {"_id": 0})
            if pub:
                result["publications"].append(pub)
        elif f["item_type"] == "expert":
            expert = await db.health_experts.find_one({"id": f["item_id"]}, {"_id": 0})
            if expert:
                result["experts"].append(expert)
    
    return result

@api_router.post("/meeting-requests")
async def create_meeting_request(request: MeetingRequestCreate, payload: dict = Depends(verify_token)):
    patient_id = payload["sub"]
    
    new_request = {
        "id": str(uuid.uuid4()),
        "patient_id": patient_id,
        "expert_id": request.expert_id,
        "status": "pending",
        "notes": request.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.meeting_requests.insert_one(new_request)
    return {"id": new_request["id"], "status": new_request["status"]}

@api_router.post("/ai/summarize")
async def summarize_content(content: dict, payload: dict = Depends(verify_token)):
    try:
        text = content.get("text", "")
        chat = LlmChat(api_key=LLM_KEY, session_id=f"summarize_{uuid.uuid4()}", system_message="You are a medical content summarizer. Provide clear, concise summaries.")
        chat.with_model("openai", "gpt-5")
        message = UserMessage(text=f"Summarize this in 2-3 sentences: {text}")
        response = await chat.send_message(message)
        return {"summary": response}
    except Exception as e:
        return {"summary": "Summary not available"}

@api_router.get("/")
async def root():
    return {"message": "CuraLink API"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
