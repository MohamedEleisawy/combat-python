from app.models.Personnage import Personnage
import random

class Florent(Personnage):
    # Liste des frappes spécifiques au personnage Florent avec leur force et expérience
    FRAPPES = [
        {"nom": "Debug", "force": 15, "exp": 6},
        {"nom": "sabotage de code", "force": 40, "exp": 10},
    ]

    def __init__(self, nom="Florent", tour="joueur2"):
        # Initialisation via le constructeur parent avec nom, frappes, et tour
        super().__init__(
            nom=nom,
            frappes=Florent.FRAPPES,
            tour=tour
        )

    def frappe(self, cible, frappe_type):
        # Sélectionne la frappe correspondant au type donné
        frappe = self.frappes[frappe_type]
        force = frappe["force"]
        exp = frappe["exp"]

        # Essai d'attaque : si la cible n'esquive pas
        if not cible.esquive():
            self.experience += exp
            # Application des dégâts sur la cible
            cible.recoit_degat(self, force)
            # Message de confirmation d'attaque réussie
            print(f"{self.nom} lance {frappe['nom']} sur {cible.nom} !")
        else:
            # Message si la cible esquive l'attaque
            print(f"{cible.nom} esquive le coup {frappe['nom']} !")

    def esquive(self):
        # Probabilité de 40% de réussir une esquive au hasard
        return random.random() < 0.40

    def recoit_degat(self, adversaire, force):
        # Calcule les dégâts totaux reçus : force + expérience de l'adversaire
        total = force + adversaire.experience
        # Ajoute ces dégâts au total déjà subi
        self.degats += total
        # Affiche les dégâts subis et leur composition
        print(f"{self.nom} subit {total} dégâts (force {force} + exp {adversaire.experience}).")
