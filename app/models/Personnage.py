from abc import ABC, abstractmethod


class Personnage(ABC):
    def __init__(self, nom, frappes, tour):
        self._nom = nom
        self._vie = 100
        self._frappes = frappes or []
        self._experience = 0
        self._degats = 0
        self.tour = tour

    # GETTERS/SETTERS avec validation
    @property
    def nom(self):
        # Retourne le nom du personnage
        return self._nom

    @nom.setter
    def nom(self, value):
        # Vérifie que le nom est une chaîne valide et suffisamment longue
        if not value or not isinstance(value, str) or len(value) < 2:
            raise ValueError("Nom invalide")
        self._nom = value

    @property
    def vie(self):
        # Retourne les points de vie actuels
        return self._vie

    @vie.setter
    def vie(self, value):
        # La vie doit rester un entier positif ou nul
        if not isinstance(value, int) or value < 0:
            raise ValueError("Vie doit être un entier positif.")
        self._vie = value

    @property
    def frappes(self):
        # Retourne la liste des attaques disponibles
        return self._frappes

    @frappes.setter
    def frappes(self, value):
        # On impose que les frappes soient toujours une liste
        if not isinstance(value, list):
            raise ValueError("frappes doit être une liste.")
        self._frappes = value

    @property
    def experience(self):
        # Retourne l'expérience accumulée
        return self._experience

    @experience.setter
    def experience(self, value):
        # L'expérience ne peut pas être négative
        if not isinstance(value, int) or value < 0:
            raise ValueError("Expérience doit être >= 0.")
        self._experience = value

    @property
    def degats(self):
        # Retourne le total des dégâts subis
        return self._degats

    @degats.setter
    def degats(self, value):
        # Les dégâts doivent être un entier positif ou nul
        if not isinstance(value, int) or value < 0:
            raise ValueError("Dégâts doit être >= 0.")
        self._degats = value

    # MÉTHODES ABSTRAITES
    @abstractmethod
    def frappe(self, cible, frappe_type):
        # Logique d'attaque d'un personnage sur une cible (implémentée dans chaque classe concrète)
        pass

    @abstractmethod
    def esquive(self): # Logique d'esquive
        pass

    @abstractmethod
    def recoit_degat(self, adversaire, force): # Logique de réception de dégâts depuis un adversaire
        pass