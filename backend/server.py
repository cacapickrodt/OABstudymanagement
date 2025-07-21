from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, date


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Sistema de Planejamento de Estudos")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models for Study Planning System
class Disciplina(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    horario_inicio: Optional[str] = None  # Format: "09:00"
    horario_fim: Optional[str] = None     # Format: "10:30"
    criado_em: datetime = Field(default_factory=datetime.utcnow)

class DisciplinaUpdate(BaseModel):
    horario_inicio: Optional[str] = None
    horario_fim: Optional[str] = None

class TarefaDiaria(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    horario: str                          # Format: "09:00"
    descricao: str
    concluida: bool = False

class TarefaDiariaCreate(BaseModel):
    horario: str
    descricao: str

class DesempenhoSemanal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    semana_inicio: date
    segunda: List[TarefaDiaria] = []
    terca: List[TarefaDiaria] = []
    quarta: List[TarefaDiaria] = []
    quinta: List[TarefaDiaria] = []
    sexta: List[TarefaDiaria] = []
    sabado: List[TarefaDiaria] = []
    domingo: List[TarefaDiaria] = []
    criado_em: datetime = Field(default_factory=datetime.utcnow)

class PlanoEstudos(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    disciplinas_ids: List[str] = []
    criado_em: datetime = Field(default_factory=datetime.utcnow)

class PlanoEstudosCreate(BaseModel):
    nome: str
    disciplinas_ids: List[str] = []

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
