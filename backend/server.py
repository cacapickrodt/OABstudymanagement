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
from datetime import datetime, date, timedelta, timedelta


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

class SessaoEstudo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    disciplina_id: str
    inicio: datetime
    fim: Optional[datetime] = None
    duracao_segundos: Optional[int] = None
    ativa: bool = True
    criado_em: datetime = Field(default_factory=datetime.utcnow)

class SessaoEstudoCreate(BaseModel):
    disciplina_id: str

class ResumoSemanalTempo(BaseModel):
    disciplina_id: str
    nome_disciplina: str
    total_segundos: int
    total_horas: float
    total_minutos: int

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

# Helper function to serialize datetime objects and MongoDB ObjectIds
def serialize_obj(obj):
    if isinstance(obj, dict):
        # Remove MongoDB _id field and serialize other fields
        return {k: serialize_obj(v) for k, v in obj.items() if k != '_id'}
    elif isinstance(obj, list):
        return [serialize_obj(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    else:
        return obj

# Initialize 19 Brazilian Law Disciplines
DISCIPLINAS_BRASILEIRAS = [
    {"nome": "Direito Constitucional"},
    {"nome": "Direito Civil"},
    {"nome": "Direito Penal"},
    {"nome": "Direito Processual Civil"},
    {"nome": "Direito Processual Penal"},
    {"nome": "Direito Administrativo"},
    {"nome": "Direito Tributário"},
    {"nome": "Direito Trabalhista"},
    {"nome": "Direito Processual Trabalhista"},
    {"nome": "Direito Empresarial"},
    {"nome": "Direito do Consumidor"},
    {"nome": "Direito Ambiental"},
    {"nome": "Direito Internacional"},
    {"nome": "Direito Previdenciário"},
    {"nome": "Direito Eleitoral"},
    {"nome": "Direito da Criança e Adolescente"},
    {"nome": "Direito de Família"},
    {"nome": "Direito das Sucessões"},
    {"nome": "Filosofia do Direito"}
]

# Startup event to initialize disciplines
@app.on_event("startup")
async def initialize_disciplines():
    # Check if disciplines already exist
    existing_count = await db.disciplinas.count_documents({})
    if existing_count == 0:
        # Insert the 19 Brazilian law disciplines
        disciplinas_to_insert = []
        for disc_data in DISCIPLINAS_BRASILEIRAS:
            disciplina = Disciplina(**disc_data)
            disciplinas_to_insert.append(disciplina.dict())
        
        if disciplinas_to_insert:
            await db.disciplinas.insert_many(disciplinas_to_insert)
            print(f"Initialized {len(disciplinas_to_insert)} disciplines")

# API Routes

# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "Sistema de Planejamento de Estudos - API"}

# Status endpoints (keeping existing ones)
@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Disciplinas endpoints
@api_router.get("/disciplinas", response_model=List[Disciplina])
async def get_disciplinas():
    """Buscar todas as disciplinas"""
    disciplinas = await db.disciplinas.find().to_list(1000)
    return [Disciplina(**serialize_obj(disciplina)) for disciplina in disciplinas]

@api_router.get("/disciplinas/{disciplina_id}", response_model=Disciplina)
async def get_disciplina(disciplina_id: str):
    """Buscar disciplina por ID"""
    disciplina = await db.disciplinas.find_one({"id": disciplina_id})
    if not disciplina:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada")
    return Disciplina(**serialize_obj(disciplina))

@api_router.put("/disciplinas/{disciplina_id}", response_model=Disciplina)
async def update_disciplina(disciplina_id: str, update_data: DisciplinaUpdate):
    """Atualizar horários de uma disciplina"""
    disciplina = await db.disciplinas.find_one({"id": disciplina_id})
    if not disciplina:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada")
    
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    if update_dict:
        await db.disciplinas.update_one(
            {"id": disciplina_id}, 
            {"$set": update_dict}
        )
    
    updated_disciplina = await db.disciplinas.find_one({"id": disciplina_id})
    return Disciplina(**serialize_obj(updated_disciplina))

# Desempenho Semanal endpoints
@api_router.get("/desempenho", response_model=List[DesempenhoSemanal])
async def get_desempenho_semanal():
    """Buscar todos os desempenhos semanais"""
    desempenhos = await db.desempenho_semanal.find().sort("semana_inicio", -1).to_list(1000)
    return [DesempenhoSemanal(**serialize_obj(desempenho)) for desempenho in desempenhos]

@api_router.get("/desempenho/{semana_inicio}")
async def get_desempenho_by_week(semana_inicio: str):
    """Buscar desempenho de uma semana específica"""
    try:
        week_date = datetime.strptime(semana_inicio, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD")
    
    desempenho = await db.desempenho_semanal.find_one({"semana_inicio": week_date.isoformat()})
    if not desempenho:
        # Create new performance week if it doesn't exist
        new_desempenho = DesempenhoSemanal(semana_inicio=week_date)
        await db.desempenho_semanal.insert_one(serialize_obj(new_desempenho.dict()))
        return serialize_obj(new_desempenho.dict())
    
    return serialize_obj(desempenho)

@api_router.post("/desempenho")
async def create_or_update_desempenho(desempenho: DesempenhoSemanal):
    """Criar ou atualizar desempenho semanal"""
    existing = await db.desempenho_semanal.find_one({"semana_inicio": desempenho.semana_inicio.isoformat()})
    
    if existing:
        # Update existing
        await db.desempenho_semanal.update_one(
            {"semana_inicio": desempenho.semana_inicio.isoformat()},
            {"$set": desempenho.dict()}
        )
    else:
        # Create new
        await db.desempenho_semanal.insert_one(desempenho.dict())
    
    return {"message": "Desempenho semanal salvo com sucesso"}

# Timer/Cronometer endpoints
@api_router.post("/timer/iniciar", response_model=SessaoEstudo)
async def iniciar_cronometro(sessao_data: SessaoEstudoCreate):
    """Iniciar cronômetro de estudo para uma disciplina"""
    # Check if there's already an active session for this discipline
    sessao_ativa = await db.sessoes_estudo.find_one({
        "disciplina_id": sessao_data.disciplina_id,
        "ativa": True
    })
    
    if sessao_ativa:
        raise HTTPException(status_code=400, detail="Já existe uma sessão ativa para esta disciplina")
    
    # Create new study session
    nova_sessao = SessaoEstudo(**sessao_data.dict(), inicio=datetime.utcnow())
    await db.sessoes_estudo.insert_one(nova_sessao.dict())
    return nova_sessao

@api_router.put("/timer/parar/{disciplina_id}")
async def parar_cronometro(disciplina_id: str):
    """Parar cronômetro de estudo para uma disciplina"""
    # Find active session
    sessao_ativa = await db.sessoes_estudo.find_one({
        "disciplina_id": disciplina_id,
        "ativa": True
    })
    
    if not sessao_ativa:
        raise HTTPException(status_code=404, detail="Nenhuma sessão ativa encontrada para esta disciplina")
    
    # Calculate duration and stop session
    fim = datetime.utcnow()
    inicio = datetime.fromisoformat(sessao_ativa["inicio"].replace('Z', '+00:00')) if isinstance(sessao_ativa["inicio"], str) else sessao_ativa["inicio"]
    duracao_segundos = int((fim - inicio).total_seconds())
    
    await db.sessoes_estudo.update_one(
        {"id": sessao_ativa["id"]},
        {
            "$set": {
                "fim": fim,
                "duracao_segundos": duracao_segundos,
                "ativa": False
            }
        }
    )
    
    return {
        "message": "Cronômetro parado com sucesso",
        "duracao_segundos": duracao_segundos,
        "duracao_formatada": f"{duracao_segundos // 3600}h {(duracao_segundos % 3600) // 60}m"
    }

@api_router.get("/timer/status/{disciplina_id}")
async def status_cronometro(disciplina_id: str):
    """Verificar status do cronômetro para uma disciplina"""
    sessao_ativa = await db.sessoes_estudo.find_one({
        "disciplina_id": disciplina_id,
        "ativa": True
    })
    
    if not sessao_ativa:
        return {"ativo": False, "sessao": None}
    
    # Calculate current duration
    inicio = datetime.fromisoformat(sessao_ativa["inicio"].replace('Z', '+00:00')) if isinstance(sessao_ativa["inicio"], str) else sessao_ativa["inicio"]
    duracao_atual = int((datetime.utcnow() - inicio).total_seconds())
    
    return {
        "ativo": True,
        "sessao": serialize_obj(sessao_ativa),
        "duracao_atual_segundos": duracao_atual
    }

@api_router.get("/timer/resumo-semanal", response_model=List[ResumoSemanalTempo])
async def resumo_tempo_semanal():
    """Obter resumo do tempo estudado por disciplina na semana atual"""
    # Calculate current week start (Monday)
    today = datetime.utcnow().date()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    
    # Convert to datetime for comparison
    week_start_dt = datetime.combine(week_start, datetime.min.time())
    week_end_dt = datetime.combine(week_end, datetime.max.time())
    
    # Aggregate time by discipline for current week
    pipeline = [
        {
            "$match": {
                "ativa": False,  # Only completed sessions
                "inicio": {
                    "$gte": week_start_dt,
                    "$lte": week_end_dt
                }
            }
        },
        {
            "$group": {
                "_id": "$disciplina_id",
                "total_segundos": {"$sum": "$duracao_segundos"}
            }
        }
    ]
    
    resultados = await db.sessoes_estudo.aggregate(pipeline).to_list(1000)
    
    # Get discipline names and format results
    resumo_final = []
    for resultado in resultados:
        disciplina = await db.disciplinas.find_one({"id": resultado["_id"]})
        if disciplina:
            total_segundos = resultado["total_segundos"]
            total_horas = total_segundos / 3600
            total_minutos = total_segundos // 60
            
            resumo_final.append(ResumoSemanalTempo(
                disciplina_id=resultado["_id"],
                nome_disciplina=disciplina["nome"],
                total_segundos=total_segundos,
                total_horas=round(total_horas, 2),
                total_minutos=total_minutos
            ))
    
    return resumo_final

@api_router.get("/timer/sessoes/{disciplina_id}")
async def get_sessoes_disciplina(disciplina_id: str):
    """Buscar todas as sessões de estudo de uma disciplina"""
    sessoes = await db.sessoes_estudo.find({"disciplina_id": disciplina_id}).sort("inicio", -1).to_list(1000)
    return [serialize_obj(sessao) for sessao in sessoes]

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
