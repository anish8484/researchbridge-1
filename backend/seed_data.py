import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def seed_database():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Check if data already exists
    existing_trials = await db.clinical_trials.count_documents({})
    if existing_trials > 0:
        print("Database already seeded")
        return
    
    # Seed Clinical Trials
    trials = [
        {
            "id": str(uuid.uuid4()),
            "nct_id": "NCT05612345",
            "title": "Immunotherapy for Advanced Brain Cancer",
            "description": "A phase III clinical trial investigating novel immunotherapy approaches for patients with advanced glioblastoma",
            "phase": "Phase 3",
            "status": "Recruiting",
            "location": "New York, USA",
            "eligibility": "Age 18-75, Diagnosed with glioblastoma",
            "contact": "research@hospital.edu",
            "conditions": ["Brain Cancer", "Glioblastoma"]
        },
        {
            "id": str(uuid.uuid4()),
            "nct_id": "NCT05723456",
            "title": "CAR-T Cell Therapy for Lung Cancer",
            "description": "Investigating CAR-T cell therapy effectiveness in treating non-small cell lung cancer",
            "phase": "Phase 2",
            "status": "Recruiting",
            "location": "Los Angeles, USA",
            "eligibility": "Age 21-80, Stage 3-4 NSCLC",
            "contact": "trials@cancercenter.org",
            "conditions": ["Lung Cancer", "NSCLC"]
        },
        {
            "id": str(uuid.uuid4()),
            "nct_id": "NCT05834567",
            "title": "Gene Therapy for Rare Blood Disorders",
            "description": "A groundbreaking study on gene therapy for treating rare hereditary blood disorders",
            "phase": "Phase 1",
            "status": "Not yet recruiting",
            "location": "Boston, USA",
            "eligibility": "Age 10+, Diagnosed genetic disorder",
            "contact": "genetics@hospital.com",
            "conditions": ["Blood Disorders", "Genetic Disorders"]
        }
    ]
    
    for trial_data in trials:
        await db.clinical_trials.insert_one(trial_data)
    
    # Seed Publications
    publications = [
        {
            "id": str(uuid.uuid4()),
            "pubmed_id": "PMID38945123",
            "title": "Novel Immunotherapy Approaches in Glioblastoma Treatment",
            "authors": ["Dr. Sarah Johnson", "Dr. Michael Chen", "Dr. Emily Rodriguez"],
            "abstract": "Recent advances in immunotherapy have opened new avenues for treating glioblastoma. This study reviews the latest checkpoint inhibitors and CAR-T therapies showing promise in clinical trials.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/38945123",
            "keywords": ["immunotherapy", "glioblastoma", "brain cancer", "CAR-T"],
            "published_date": "2024-03-15"
        },
        {
            "id": str(uuid.uuid4()),
            "pubmed_id": "PMID38956234",
            "title": "Advances in Non-Small Cell Lung Cancer Treatment",
            "authors": ["Dr. Robert Williams", "Dr. Lisa Martinez", "Dr. James Lee"],
            "abstract": "This comprehensive review examines targeted therapies and immunotherapies that have transformed NSCLC treatment over the past five years.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/38956234",
            "keywords": ["lung cancer", "NSCLC", "targeted therapy", "immunotherapy"],
            "published_date": "2024-02-20"
        },
        {
            "id": str(uuid.uuid4()),
            "pubmed_id": "PMID38967345",
            "title": "Gene Therapy Breakthroughs in Rare Diseases",
            "authors": ["Dr. Amanda Foster", "Dr. David Park", "Dr. Rachel Green"],
            "abstract": "Gene therapy has emerged as a revolutionary approach for treating previously incurable genetic disorders. This paper discusses recent FDA approvals and ongoing clinical trials.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/38967345",
            "keywords": ["gene therapy", "rare diseases", "genetic disorders", "CRISPR"],
            "published_date": "2024-01-10"
        }
    ]
    
    for pub_data in publications:
        await db.publications.insert_one(pub_data)
    
    # Seed Health Experts
    experts = [
        {
            "id": str(uuid.uuid4()),
            "name": "Dr. Sarah Johnson",
            "specialty": ["Neuro-Oncology", "Brain Cancer"],
            "research_interests": ["Immunotherapy", "Glioblastoma", "Clinical Trials"],
            "is_registered": False,
            "bio": "Leading neuro-oncologist with 15 years of experience in brain cancer research"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Dr. Michael Chen",
            "specialty": ["Oncology", "Lung Cancer"],
            "research_interests": ["CAR-T Therapy", "Immunotherapy", "Precision Medicine"],
            "is_registered": False,
            "bio": "Expert in lung cancer treatment and immunotherapy research"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Dr. Emily Rodriguez",
            "specialty": ["Genetics", "Gene Therapy"],
            "research_interests": ["Gene Editing", "CRISPR", "Rare Diseases"],
            "is_registered": False,
            "bio": "Pioneer in gene therapy for rare genetic disorders"
        }
    ]
    
    for expert_data in experts:
        expert = HealthExpert(**expert_data)
        db.add(expert)
    
    # Seed Forums
    forums = [
        {
            "id": str(uuid.uuid4()),
            "category": "Cancer Research",
            "title": "Latest Advances in Immunotherapy",
            "description": "Discuss recent breakthroughs in cancer immunotherapy"
        },
        {
            "id": str(uuid.uuid4()),
            "category": "Clinical Trials",
            "title": "Patient Experiences with Clinical Trials",
            "description": "Share your experiences and questions about participating in clinical trials"
        },
        {
            "id": str(uuid.uuid4()),
            "category": "Gene Therapy",
            "title": "Gene Therapy for Rare Diseases",
            "description": "Discussion on emerging gene therapy treatments"
        }
    ]
    
    for forum_data in forums:
        forum = Forum(**forum_data)
        db.add(forum)
    
    db.commit()
    print("Database seeded successfully!")
    db.close()

if __name__ == "__main__":
    seed_database()
