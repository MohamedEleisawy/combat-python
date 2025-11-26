import sys
import time


def slow_print(text, delay=0.03):
    """
    Affiche le texte lentement caractère par caractère avec un délai pour effet dramatique.
    """
    for c in text:
        print(c, end='', flush=True)
        time.sleep(delay)
    print()  # retour à la ligne


def colorize(text, color):
    """
    Colore le texte avec les codes ANSI selon la couleur demandée.
    Couleurs supportées : rouge, vert, jaune, bleu, violet, cyan, gris.
    """
    colors = {
        'rouge': '\033[91m',
        'vert': '\033[92m',
        'jaune': '\033[93m',
        'bleu': '\033[94m',
        'violet': '\033[95m',
        'cyan': '\033[96m',
        'gris': '\033[90m',
        'reset': '\033[0m',
    }
    return f"{colors.get(color, colors['reset'])}{text}{colors['reset']}"


def icone_frappe(type_str):
    """
    Renvoie un icone Unicode selon le nom de la frappe.
    Icônes pour Jc (pilote) et Florent (dev cinéma).
    """
    icones = {
        # Jc - pilote
        'Manœuvre éclair': '✈️',
        'Tir de précision': '🎯',
        # Florent - développeur cinéma
        'Debug magistral': '🛠️',
        'Scène d’action': '🎬',
    }
    return icones.get(type_str, '🗡')


def barre_de_vie(vie, degats):
    """
    Affiche les points de vie restants sous la forme "PV restants / PV totaux".
    Vie ne peut pas être négative.
    """
    total = vie
    restant = max(0, vie - degats)
    return f"{restant}/{total}"


def encadre(msg):
    """
    Encadre un message par des flèches et colore en jaune pour mise en valeur.
    """
    return colorize(f"=> {msg} <=", 'jaune')
