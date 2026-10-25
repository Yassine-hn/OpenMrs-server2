from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class OperativeReportRequest(BaseModel):
    patient_id: Optional[str] = Field(None, description="Identifiant du patient (ex: N° dossier)")
    patient_name: Optional[str] = Field(None, description="Nom et prénom du patient")
    age: Optional[int] = Field(None, description="Âge du patient")
    gender: Optional[str] = Field(None, description="Genre (M/F)")
    
    intervention: str = Field(..., description="Nom de l'intervention réalisée")
    urgence: Optional[str] = Field("Programmée", description="Programmée ou Urgente")
    cote: Optional[str] = Field(None, description="Droit, Gauche, Bilatéral, Médian, Non applicable")
    indication: str = Field(..., description="Indication opératoire")
    diagnostic_preop: Optional[str] = Field(None, description="Diagnostic pré-opératoire")
    diagnostic_postop: Optional[str] = Field(None, description="Diagnostic post-opératoire")
    
    operateurs: Optional[str] = Field(None, description="Chirurgien(s) opérateur(s)")
    aides: Optional[str] = Field(None, description="Aide(s) opératoire(s)")
    anesthesiste: Optional[str] = Field(None, description="Médecin anesthésiste")
    type_anesthesie: Optional[str] = Field("Anesthésie générale", description="Type d'anesthésie")
    
    installation: Optional[str] = Field("Décubitus dorsal", description="Position du patient")
    voie_abord: Optional[str] = Field(None, description="Voie d'abord")
    neuronavigation: Optional[bool] = Field(False, description="Utilisation de la neuronavigation")
    microscope: Optional[bool] = Field(False, description="Utilisation du microscope opératoire")
    
    constatations: Optional[str] = Field(None, description="Constatations per-opératoires")
    description_geste: Optional[str] = Field(None, description="Description détaillée du geste opératoire")
    qualite_exerese: Optional[str] = Field(None, description="Exérèse complète, subtotale, partielle, Biopsie")
    prelevement_anapath: Optional[bool] = Field(False, description="Prélèvement envoyé en anapath")
    materiel_implante: Optional[str] = Field(None, description="Matériel implanté (valve de dérivation, ostéosynthèse...)")
    
    pertes_sanguines_ml: Optional[int] = Field(None, description="Pertes sanguines estimées en mL")
    transfusion: Optional[bool] = Field(False, description="Transfusion per-opératoire")
    complications: Optional[str] = Field(None, description="Incidents ou complications per-opératoires")
    drainage: Optional[str] = Field(None, description="Type de drainage laissé en place")
    fermeture: Optional[str] = Field(None, description="Mode de fermeture")
    consignes_postop: Optional[str] = Field(None, description="Consignes post-opératoires et surveillance")

class ConsultationRequest(BaseModel):
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    
    motif: str = Field(..., description="Motif de la consultation")
    histoire_maladie: Optional[str] = Field(None, description="Histoire de la maladie")
    antecedents: Optional[str] = Field(None, description="Antécédents médicaux et chirurgicaux")
    examen_clinique: Optional[str] = Field(None, description="Examen neurologique et général (GCS, déficit...)")
    imagerie: Optional[str] = Field(None, description="Données d'imagerie TDM / IRM")
    conclusion: Optional[str] = Field(None, description="Conclusion / Hypothèses diagnostiques")
    cat: Optional[str] = Field(None, description="Conduite à tenir (traitement, programmation chirurgicale, examens complémentaires)")

class DischargeLetterRequest(BaseModel):
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    age: Optional[int] = None
    date_admission: Optional[str] = None
    date_sortie: Optional[str] = None
    
    diagnostic_principal: str = Field(..., description="Diagnostic principal de sortie")
    resume_hospitalisation: str = Field(..., description="Résumé de l'hospitalisation et des gestes réalisés")
    evolution_clinique: Optional[str] = Field(None, description="Évolution post-opératoire et état clinique à la sortie")
    traitement_sortie: Optional[str] = Field(None, description="Ordonnance / traitement de sortie")
    consignes_et_suivi: Optional[str] = Field(None, description="Rendez-vous de contrôle, ablation des fils, arrêt de travail")

class DraftResponse(BaseModel):
    document_type: str
    draft_text: str
    model_used: str
    latency_ms: float

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    patient_context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    model: str
    latency_ms: float

class TranscribeResponse(BaseModel):
    text: str
    duration_seconds: Optional[float] = None
    language: str = "fr"
