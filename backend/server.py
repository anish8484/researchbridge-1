from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, Enum, ForeignKey, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import jwt
from passlib.context import CryptContext
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage
import aiohttp

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# PostgreSQL connection
postgres_url = os.environ['POSTGRES_URL']
engine = create_engine(postgres_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# JWT settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 72

# LLM setup
LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    user_type = Column(Enum('patient', 'researcher', name='user_types'), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class PatientProfile(Base):
    __tablename__ = "patient_profiles"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    conditions = Column(JSON)
    location = Column(String)
    raw_input = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ResearcherProfile(Base):
    __tablename__ = "researcher_profiles"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    specialties = Column(JSON)
    research_interests = Column(JSON)
    orcid = Column(String)
    researchgate = Column(String)
    availability = Column(Boolean, default=False)
    bio = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ClinicalTrial(Base):
    __tablename__ = "clinical_trials"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nct_id = Column(String, unique=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    phase = Column(String)
    status = Column(String)
    location = Column(String)
    eligibility = Column(Text)
    contact = Column(String)
    conditions = Column(JSON)
    created_by = Column(String, ForeignKey('users.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Publication(Base):
    __tablename__ = "publications"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pubmed_id = Column(String)
    title = Column(Text, nullable=False)
    authors = Column(JSON)
    abstract = Column(Text)
    url = Column(String)
    keywords = Column(JSON)
    published_date = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class HealthExpert(Base):
    __tablename__ = "health_experts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=True)
    name = Column(String, nullable=False)
    specialty = Column(JSON)
    research_interests = Column(JSON)
    contact = Column(String)
    is_registered = Column(Boolean, default=False)
    bio = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    item_type = Column(String, nullable=False)
    item_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Forum(Base):
    __tablename__ = "forums"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    created_by = Column(String, ForeignKey('users.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ForumPost(Base):
    __tablename__ = "forum_posts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    forum_id = Column(String, ForeignKey('forums.id'), nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(String, ForeignKey('forum_posts.id'), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    from_user = Column(String, ForeignKey('users.id'), nullable=False)
    to_user = Column(String, ForeignKey('users.id'), nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ConnectionRequest(Base):
    __tablename__ = "connection_requests"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    from_user = Column(String, ForeignKey('users.id'), nullable=False)
    to_user = Column(String, ForeignKey('users.id'), nullable=False)
    status = Column(Enum('pending', 'accepted', 'rejected', name='request_status'), default='pending')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class MeetingRequest(Base):
    __tablename__ = "meeting_requests"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey('users.id'), nullable=False)
    expert_id = Column(String, nullable=False)
    status = Column(Enum('pending', 'approved', 'rejected', name='meeting_status'), default='pending')
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class PasswordReset(Base):
    __tablename__ = "password_resets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, nullable=False)
    reset_code = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = pwd_context.hash(user_data.password)
    new_user = User(
        id=str(uuid.uuid4()),
        email=user_data.email,
        password_hash=hashed_password,
        user_type=user_data.user_type
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    token = create_access_token(new_user.id, new_user.user_type)
    return {"token": token, "user_id": new_user.id, "user_type": new_user.user_type}

@api_router.post("/auth/login")
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not pwd_context.verify(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(user.id, user.user_type)
    return {"token": token, "user_id": user.id, "user_type": user.user_type}

@api_router.get("/auth/me")
async def get_me(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "user_type": user.user_type}

@api_router.post("/patients/profile")
async def create_patient_profile(profile: PatientProfileCreate, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
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
    
    existing = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if existing:
        existing.conditions = conditions
        existing.location = profile.location
        existing.raw_input = profile.raw_input
        db.commit()
        return {"id": existing.id, "conditions": conditions}
    
    new_profile = PatientProfile(
        id=str(uuid.uuid4()),
        user_id=user_id,
        conditions=conditions,
        location=profile.location,
        raw_input=profile.raw_input
    )
    db.add(new_profile)
    db.commit()
    return {"id": new_profile.id, "conditions": conditions}

@api_router.get("/patients/dashboard")
async def get_patient_dashboard(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user_id = payload["sub"]
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    
    if not profile:
        return {"profile": None, "recommendations": []}
    
    trials = db.query(ClinicalTrial).limit(5).all()
    publications = db.query(Publication).limit(5).all()
    experts = db.query(HealthExpert).limit(5).all()
    
    return {
        "profile": {
            "conditions": profile.conditions,
            "location": profile.location
        },
        "trials": [{"id": t.id, "title": t.title, "status": t.status, "location": t.location} for t in trials],
        "publications": [{"id": p.id, "title": p.title, "authors": p.authors} for p in publications],
        "experts": [{"id": e.id, "name": e.name, "specialty": e.specialty} for e in experts]
    }

@api_router.get("/patients/experts")
async def get_health_experts(specialty: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(HealthExpert)
    experts = query.limit(20).all()
    return [{"id": e.id, "name": e.name, "specialty": e.specialty, "research_interests": e.research_interests, "is_registered": e.is_registered} for e in experts]

@api_router.get("/patients/clinical-trials")
async def search_clinical_trials(query: Optional[str] = None, status: Optional[str] = None, location: Optional[str] = None, db: Session = Depends(get_db)):
    # Mock clinical trials from database
    trials_query = db.query(ClinicalTrial)
    if status:
        trials_query = trials_query.filter(ClinicalTrial.status == status)
    trials = trials_query.limit(20).all()
    return [{"id": t.id, "nct_id": t.nct_id, "title": t.title, "description": t.description, "status": t.status, "phase": t.phase, "location": t.location} for t in trials]

@api_router.get("/patients/publications")
async def search_publications(query: Optional[str] = None, db: Session = Depends(get_db)):
    publications = db.query(Publication).limit(20).all()
    return [{"id": p.id, "title": p.title, "authors": p.authors, "abstract": p.abstract, "url": p.url, "published_date": p.published_date} for p in publications]

@api_router.post("/researchers/profile")
async def create_researcher_profile(profile: ResearcherProfileCreate, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user_id = payload["sub"]
    
    existing = db.query(ResearcherProfile).filter(ResearcherProfile.user_id == user_id).first()
    if existing:
        existing.specialties = profile.specialties
        existing.research_interests = profile.research_interests
        existing.orcid = profile.orcid
        existing.researchgate = profile.researchgate
        existing.availability = profile.availability
        existing.bio = profile.bio
        db.commit()
        return {"id": existing.id}
    
    new_profile = ResearcherProfile(
        id=str(uuid.uuid4()),
        user_id=user_id,
        specialties=profile.specialties,
        research_interests=profile.research_interests,
        orcid=profile.orcid,
        researchgate=profile.researchgate,
        availability=profile.availability,
        bio=profile.bio
    )
    db.add(new_profile)
    db.commit()
    
    # Also create health expert entry
    user = db.query(User).filter(User.id == user_id).first()
    expert = HealthExpert(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=user.email.split('@')[0],
        specialty=profile.specialties,
        research_interests=profile.research_interests,
        is_registered=True,
        bio=profile.bio
    )
    db.add(expert)
    db.commit()
    
    return {"id": new_profile.id}

@api_router.get("/researchers/dashboard")
async def get_researcher_dashboard(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user_id = payload["sub"]
    profile = db.query(ResearcherProfile).filter(ResearcherProfile.user_id == user_id).first()
    
    trials = db.query(ClinicalTrial).filter(ClinicalTrial.created_by == user_id).all()
    forums = db.query(Forum).filter(Forum.created_by == user_id).all()
    
    return {
        "profile": {
            "specialties": profile.specialties if profile else [],
            "research_interests": profile.research_interests if profile else []
        },
        "trials": [{"id": t.id, "title": t.title, "status": t.status} for t in trials],
        "forums": [{"id": f.id, "title": f.title, "category": f.category} for f in forums]
    }

@api_router.get("/researchers/collaborators")
async def get_collaborators(specialty: Optional[str] = None, db: Session = Depends(get_db)):
    researchers = db.query(User).filter(User.user_type == 'researcher').limit(20).all()
    result = []
    for r in researchers:
        profile = db.query(ResearcherProfile).filter(ResearcherProfile.user_id == r.id).first()
        if profile:
            result.append({
                "id": r.id,
                "name": r.email.split('@')[0],
                "specialties": profile.specialties,
                "research_interests": profile.research_interests
            })
    return result

@api_router.post("/researchers/clinical-trials")
async def create_clinical_trial(trial: ClinicalTrialCreate, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user_id = payload["sub"]
    
    new_trial = ClinicalTrial(
        id=str(uuid.uuid4()),
        nct_id=f"NCT{uuid.uuid4().hex[:8].upper()}",
        title=trial.title,
        description=trial.description,
        phase=trial.phase,
        status=trial.status,
        location=trial.location,
        eligibility=trial.eligibility,
        contact=trial.contact,
        conditions=trial.conditions,
        created_by=user_id
    )
    db.add(new_trial)
    db.commit()
    return {"id": new_trial.id, "nct_id": new_trial.nct_id}

@api_router.put("/researchers/clinical-trials/{trial_id}")
async def update_clinical_trial(trial_id: str, trial: ClinicalTrialCreate, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    existing = db.query(ClinicalTrial).filter(ClinicalTrial.id == trial_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    existing.title = trial.title
    existing.description = trial.description
    existing.phase = trial.phase
    existing.status = trial.status
    existing.location = trial.location
    existing.eligibility = trial.eligibility
    existing.contact = trial.contact
    existing.conditions = trial.conditions
    db.commit()
    return {"id": existing.id}

@api_router.post("/connection-requests")
async def create_connection_request(request: ConnectionRequestCreate, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    from_user = payload["sub"]
    
    existing = db.query(ConnectionRequest).filter(
        ConnectionRequest.from_user == from_user,
        ConnectionRequest.to_user == request.to_user
    ).first()
    
    if existing:
        return {"id": existing.id, "status": existing.status}
    
    new_request = ConnectionRequest(
        id=str(uuid.uuid4()),
        from_user=from_user,
        to_user=request.to_user
    )
    db.add(new_request)
    db.commit()
    return {"id": new_request.id, "status": new_request.status}

@api_router.get("/connection-requests")
async def get_connection_requests(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user_id = payload["sub"]
    requests = db.query(ConnectionRequest).filter(
        (ConnectionRequest.from_user == user_id) | (ConnectionRequest.to_user == user_id)
    ).all()
    return [{"id": r.id, "from_user": r.from_user, "to_user": r.to_user, "status": r.status} for r in requests]

@api_router.post("/forums")
async def create_forum(forum: ForumCreate, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user_id = payload["sub"]
    
    new_forum = Forum(
        id=str(uuid.uuid4()),
        category=forum.category,
        title=forum.title,
        description=forum.description,
        created_by=user_id
    )
    db.add(new_forum)
    db.commit()
    return {"id": new_forum.id}

@api_router.get("/forums")
async def get_forums(category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Forum)
    if category:
        query = query.filter(Forum.category == category)
    forums = query.all()
    return [{"id": f.id, "category": f.category, "title": f.title, "description": f.description} for f in forums]

@api_router.post("/forums/posts")
async def create_forum_post(post: ForumPostCreate, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user_id = payload["sub"]
    
    new_post = ForumPost(
        id=str(uuid.uuid4()),
        forum_id=post.forum_id,
        user_id=user_id,
        content=post.content,
        parent_id=post.parent_id
    )
    db.add(new_post)
    db.commit()
    return {"id": new_post.id}

@api_router.get("/forums/{forum_id}/posts")
async def get_forum_posts(forum_id: str, db: Session = Depends(get_db)):
    posts = db.query(ForumPost).filter(ForumPost.forum_id == forum_id).all()
    return [{"id": p.id, "user_id": p.user_id, "content": p.content, "parent_id": p.parent_id, "created_at": p.created_at.isoformat()} for p in posts]

@api_router.post("/chat/messages")
async def send_message(message: MessageCreate, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    from_user = payload["sub"]
    
    new_message = Message(
        id=str(uuid.uuid4()),
        from_user=from_user,
        to_user=message.to_user,
        message=message.message
    )
    db.add(new_message)
    db.commit()
    return {"id": new_message.id}

@api_router.get("/chat/messages/{user_id}")
async def get_messages(user_id: str, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    current_user = payload["sub"]
    messages = db.query(Message).filter(
        ((Message.from_user == current_user) & (Message.to_user == user_id)) |
        ((Message.from_user == user_id) & (Message.to_user == current_user))
    ).order_by(Message.created_at).all()
    return [{"id": m.id, "from_user": m.from_user, "to_user": m.to_user, "message": m.message, "created_at": m.created_at.isoformat()} for m in messages]

@api_router.post("/favorites")
async def add_favorite(favorite: FavoriteCreate, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user_id = payload["sub"]
    
    existing = db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.item_type == favorite.item_type,
        Favorite.item_id == favorite.item_id
    ).first()
    
    if existing:
        db.delete(existing)
        db.commit()
        return {"removed": True}
    
    new_favorite = Favorite(
        id=str(uuid.uuid4()),
        user_id=user_id,
        item_type=favorite.item_type,
        item_id=favorite.item_id
    )
    db.add(new_favorite)
    db.commit()
    return {"id": new_favorite.id, "added": True}

@api_router.get("/favorites")
async def get_favorites(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user_id = payload["sub"]
    favorites = db.query(Favorite).filter(Favorite.user_id == user_id).all()
    
    result = {"trials": [], "publications": [], "experts": []}
    for f in favorites:
        if f.item_type == "trial":
            trial = db.query(ClinicalTrial).filter(ClinicalTrial.id == f.item_id).first()
            if trial:
                result["trials"].append({"id": trial.id, "title": trial.title, "status": trial.status})
        elif f.item_type == "publication":
            pub = db.query(Publication).filter(Publication.id == f.item_id).first()
            if pub:
                result["publications"].append({"id": pub.id, "title": pub.title, "authors": pub.authors})
        elif f.item_type == "expert":
            expert = db.query(HealthExpert).filter(HealthExpert.id == f.item_id).first()
            if expert:
                result["experts"].append({"id": expert.id, "name": expert.name, "specialty": expert.specialty})
    
    return result

@api_router.post("/meeting-requests")
async def create_meeting_request(request: MeetingRequestCreate, payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    patient_id = payload["sub"]
    
    new_request = MeetingRequest(
        id=str(uuid.uuid4()),
        patient_id=patient_id,
        expert_id=request.expert_id,
        notes=request.notes
    )
    db.add(new_request)
    db.commit()
    return {"id": new_request.id, "status": new_request.status}

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