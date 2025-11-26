from app.models.Personnage import Personnage
import random


class Jc(Personnage):
    # Frappes spécifiques du pilote Jc (force, expérience)
    FRAPPES = [
        {"nom": "Parler en anglais", "force": 20, "exp": 5},
        {"nom": "Tir de précision en avion", "force": 30, "exp": 10},
    ]

    def __init__(self, nom="Jc", tour="joueur1"):
        super().__init__(
            nom=nom,
            frappes=Jc.FRAPPES,
            tour=tour
        )

    def frappe(self, cible, frappe_type):
        frappe = self.frappes[frappe_type]
        force = frappe["force"]
        exp = frappe["exp"]

        # Coup : on tente une esquive adverse
        if not cible.esquive():
            self.experience += exp
            cible.recoit_degat(self, force)
            print(f"{self.nom} exécute {frappe['nom']} sur {cible.nom} !")
        else:
            print(f"{cible.nom} esquive la manœuvre {frappe['nom']} !")

    def esquive(self):
        # 30% de chance d'esquive
        return random.random() < 0.3

    def recoit_degat(self, adversaire, force):
        # On reçoit (force de frappe + expérience adverse)
        total = force + adversaire.experience
        self.degats += total
        print(f"{self.nom} reçoit {total} dégâts (force {force} + exp {adversaire.experience}).")
