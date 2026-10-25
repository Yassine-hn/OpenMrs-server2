import pytest
from app.schemas import OperativeReportRequest, ConsultationRequest, DischargeLetterRequest
from app.prompts import build_operative_report_prompt, build_consultation_prompt, build_discharge_prompt

def test_operative_report_prompt_structure():
    req = OperativeReportRequest(
        patient_name="Benali Mohamed",
        age=45,
        gender="M",
        patient_id="CHU-NC-2026-0042",
        intervention="Craniotomie et exérèse d'un méningiome de la convexité",
        urgence="Programmée",
        cote="Droit",
        indication="Méningiome frontal droit symptomatique",
        diagnostic_preop="Méningiome frontal droit",
        diagnostic_postop="Exérèse complète de méningiome frontal droit (Simpson I)",
        operateurs="Dr. Amrani",
        anesthesiste="Dr. Khelifi",
        voie_abord="Voie coronale frontale droite",
        neuronavigation=True,
        microscope=True,
        constatations="Tumeur extra-axiale bien limitée, adhérente à la dure-mère frontale.",
        description_geste="Volet fronto-temporale droit, ouverture durale en U...",
        qualite_exerese="Exérèse complète",
        prelevement_anapath=True,
        pertes_sanguines_ml=250,
        transfusion=False,
        drainage="Redon aspiratif sous-cutané"
    )
    prompt = build_operative_report_prompt(req)
    assert "Benali Mohamed" in prompt
    assert "Craniotomie et exérèse d'un méningiome" in prompt
    assert "Neuronavigation: Oui" in prompt
    assert "Microscope opératoire: Oui" in prompt
    assert "Pertes sanguines estimées: 250 mL" in prompt

def test_consultation_prompt_structure():
    req = ConsultationRequest(
        patient_name="Boudiaf Fatima",
        age=52,
        gender="F",
        motif="Céphalées progressives et hémiparésie gauche",
        histoire_maladie="Évolution depuis 2 mois...",
        examen_clinique="GCS 15, déficit moteur brachio-facial gauche côté 4/5.",
        imagerie="IRM cérébrale montrant une lésion temporo-pariétale droite.",
        conclusion="Processus expansif intracrânien droit probable gliome de haut grade.",
        cat="Indication chirurgicale retenue, bilan pré-anesthésique."
    )
    prompt = build_consultation_prompt(req)
    assert "Boudiaf Fatima" in prompt
    assert "Céphalées progressives" in prompt
    assert "GCS 15" in prompt
    assert "IRM cérébrale" in prompt

def test_discharge_prompt_structure():
    req = DischargeLetterRequest(
        patient_name="Rahmani Karim",
        age=38,
        diagnostic_principal="Hématome sous-dural aigu post-traumatique opéré",
        resume_hospitalisation="Évacuation chirurgicale par volet décompressif à J1...",
        evolution_clinique="Bonne récupération, GCS 15 sans déficit résiduel.",
        traitement_sortie="Paracétamol 1g si douleur, Lovenox 0.4 pendant 7 jours.",
        consignes_et_suivi="Ablation des fils à J10, consultation de contrôle dans 1 mois."
    )
    prompt = build_discharge_prompt(req)
    assert "Rahmani Karim" in prompt
    assert "Hématome sous-dural" in prompt
    assert "Paracétamol" in prompt
