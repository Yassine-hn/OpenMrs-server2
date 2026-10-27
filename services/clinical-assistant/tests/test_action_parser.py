import unittest
from app.main import extract_action_proposal

class TestActionParser(unittest.TestCase):
    def test_extract_update_address(self):
        p1 = "Modifie l'adresse du patient : 15 Rue des Martyrs, Blida"
        act1 = extract_action_proposal(p1)
        self.assertIsNotNone(act1)
        self.assertEqual(act1.action_type, "update_patient_address")
        self.assertEqual(act1.parameters["address1"], "15 Rue des Martyrs")
        self.assertEqual(act1.parameters["cityVillage"], "Blida")

        p2 = "Change l'adresse du patient à Centre Ville"
        act2 = extract_action_proposal(p2)
        self.assertIsNotNone(act2)
        self.assertEqual(act2.action_type, "update_patient_address")
        self.assertEqual(act2.parameters["address1"], "Centre Ville")

        p3 = "Modifie l adresse du patient : 15 Rue des Martyrs, Blida"
        act3 = extract_action_proposal(p3)
        self.assertIsNotNone(act3)
        self.assertEqual(act3.action_type, "update_patient_address")
        self.assertEqual(act3.parameters["address1"], "15 Rue des Martyrs")
        self.assertEqual(act3.parameters["cityVillage"], "Blida")

        p4 = "Modifier l’adresse du patient: Bab Ezzouar, Alger"
        act4 = extract_action_proposal(p4)
        self.assertIsNotNone(act4)
        self.assertEqual(act4.action_type, "update_patient_address")
        self.assertEqual(act4.parameters["address1"], "Bab Ezzouar")
        self.assertEqual(act4.parameters["cityVillage"], "Alger")

    def test_extract_record_clinical_note(self):
        p = "Enregistre une note de consultation : Examen neurologique stable, GCS 15/15, aucun déficit."
        act = extract_action_proposal(p)
        self.assertIsNotNone(act)
        self.assertEqual(act.action_type, "record_clinical_note")
        self.assertIn("Examen neurologique stable", act.parameters["note"])
        self.assertEqual(act.parameters["encounter_type"], "1f331153-e484-554a-9184-1d45a2399166")

        p2 = "Ajouter une note clinique: Patient réveillé et coopérant."
        act2 = extract_action_proposal(p2)
        self.assertIsNotNone(act2)
        self.assertEqual(act2.action_type, "record_clinical_note")
        self.assertIn("Patient réveillé et coopérant", act2.parameters["note"])

    def test_extract_add_clinical_diagnosis(self):
        p = "Ajoute le diagnostic : Méningiome de la convexité frontale droite"
        act = extract_action_proposal(p)
        self.assertIsNotNone(act)
        self.assertEqual(act.action_type, "add_clinical_diagnosis")
        self.assertEqual(act.parameters["diagnosis"], "Méningiome de la convexité frontale droite")

        p2 = "Poser le diagnostic d'adénome hypophysaire"
        act2 = extract_action_proposal(p2)
        self.assertIsNotNone(act2)
        self.assertEqual(act2.action_type, "add_clinical_diagnosis")
        self.assertIn("adénome hypophysaire", act2.parameters["diagnosis"])

    def test_regular_question_has_no_action(self):
        p = "Quel est le protocole d'antibiothérapie pour une craniotomie programmée ?"
        act = extract_action_proposal(p)
        self.assertIsNone(act)

if __name__ == "__main__":
    unittest.main()
