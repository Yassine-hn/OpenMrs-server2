from .schemas import ConsultationRequest, DischargeLetterRequest, OperativeReportRequest

SYSTEM_PROMPT = """Tu es un assistant médical spécialisé en neurochirurgie pour le service de neurochirurgie du CHU Frantz Fanon de Blida.
Ton rôle est de rédiger des comptes-rendus médicaux rigoureux, clairs, en français médical académique standard, à partir des données structurées fournies par le médecin.
Ne jamais inventer d'éléments factuels ou cliniques non mentionnés. Respecte scrupuleusement la structure demandée.
Le texte produit est un projet de compte-rendu soumis à la validation et signature du médecin responsable."""

def build_operative_report_prompt(req: OperativeReportRequest) -> str:
    patient_info = []
    if req.patient_name:
        patient_info.append(f"Patient: {req.patient_name}")
    if req.age:
        patient_info.append(f"Âge: {req.age} ans")
    if req.gender:
        patient_info.append(f"Genre: {req.gender}")
    if req.patient_id:
        patient_info.append(f"N° Dossier: {req.patient_id}")
    patient_header = " | ".join(patient_info) if patient_info else "Non spécifié"

    prompt = f"""Rédige un compte-rendu opératoire complet et structuré en français pour l'intervention neurochirurgicale suivante :

Informations administratives:
- {patient_header}
- Caractère: {req.urgence}
- Opérateur: {req.operateurs or 'Non renseigné'}
- Aides: {req.aides or 'Non renseigné'}
- Anesthésie: {req.anesthesiste or 'Équipe anesthésie'} ({req.type_anesthesie})

Données opératoires:
- Intervention: {req.intervention} (Côté: {req.cote or 'Non précisé'})
- Indication opératoire: {req.indication}
- Diagnostic pré-opératoire: {req.diagnostic_preop or req.indication}
- Diagnostic post-opératoire: {req.diagnostic_postop or req.diagnostic_preop or 'Idem'}
- Installation: {req.installation}
- Voie d'abord: {req.voie_abord or 'Standard'}
- Neuronavigation: {'Oui' if req.neuronavigation else 'Non'}
- Microscope opératoire: {'Oui' if req.microscope else 'Non'}
- Constatations per-opératoires: {req.constatations or 'Non précisées'}
- Description du geste: {req.description_geste or 'Geste habituel selon les règles de l art'}
- Qualité de l'exérèse: {req.qualite_exerese or 'Non précisée'}
- Prélèvement anatomopathologique: {'Oui' if req.prelevement_anapath else 'Non'}
- Matériel implanté: {req.materiel_implante or 'Aucun'}
- Pertes sanguines estimées: {f'{req.pertes_sanguines_ml} mL' if req.pertes_sanguines_ml is not None else 'Minimes'}
- Transfusion: {'Oui' if req.transfusion else 'Non'}
- Incidents / Complications: {req.complications or 'Aucun incident per-opératoire à signaler'}
- Drainage: {req.drainage or 'Aucun'}
- Fermeture: {req.fermeture or 'Plan par plan'}
- Consignes post-opératoires: {req.consignes_postop or 'Surveillance neurologique horaire standard'}

Format attendu:
1. TITRE ET INFORMATIONS GÉNÉRALES
2. INDICATION ET DIAGNOSTICS
3. TECHNIQUE OPÉRATOIRE DÉTAILLÉE (Installation, abord, temps opératoires, constatations)
4. FIN D'INTERVENTION ET SUITES IMMÉDIATES (Pertes, drainage, consignes)"""
    return prompt

def build_consultation_prompt(req: ConsultationRequest) -> str:
    prompt = f"""Rédige une observation clinique de consultation neurochirurgicale structurée en français :

Données patient:
- Patient: {req.patient_name or 'Anonyme'}, {f'{req.age} ans' if req.age else ''} ({req.gender or ''})
- Motif: {req.motif}
- Histoire de la maladie: {req.histoire_maladie or 'Non documentée'}
- Antécédents: {req.antecedents or 'Sans particularité'}
- Examen clinique: {req.examen_clinique or 'Examen neurologique sans déficit franc'}
- Imagerie: {req.imagerie or 'Non fournie'}
- Conclusion / Hypothèses: {req.conclusion or 'À préciser'}
- Conduite à tenir: {req.cat or 'Poursuite de la prise en charge'}

Format attendu:
- MOTIF ET HISTOIRE DE LA MALADIE
- ANTÉCÉDENTS
- EXAMEN PHYSIQUE ET NEUROLOGIQUE
- SYNTHÈSE DE L'IMAGERIE
- CONCLUSION ET CONDUITE À TENIR"""
    return prompt

def build_discharge_prompt(req: DischargeLetterRequest) -> str:
    prompt = f"""Rédige un compte-rendu d'hospitalisation et une lettre de sortie médicale en neurochirurgie :

Informations:
- Patient: {req.patient_name or 'Patient'}, {f'{req.age} ans' if req.age else ''}
- Période: Du {req.date_admission or 'Admission'} au {req.date_sortie or 'Sortie'}
- Diagnostic principal: {req.diagnostic_principal}
- Résumé de l'hospitalisation: {req.resume_hospitalisation}
- Évolution clinique: {req.evolution_clinique or 'Favorable, suites opératoires simples'}
- Traitement de sortie: {req.traitement_sortie or 'Ordonnance standard'}
- Consignes et suivi: {req.consignes_et_suivi or 'Consultation de contrôle prévue'}

Format attendu:
- IDENTIFICATION ET DIAGNOSTIC PRINCIPAL
- RÉSUMÉ DE L'HOSPITALISATION ET GESTES PRATIQUÉS
- ÉVOLUTION CLINIQUE ET ÉTAT À LA SORTIE
- CONDUITE À TENIR, TRAITEMENT ET RENDEZ-VOUS DE CONTRÔLE"""
    return prompt
