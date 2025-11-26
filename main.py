from app.models.Jc import Jc
from app.models.Florent import Florent
from app.services.utils import colorize, icone_frappe, barre_de_vie, encadre, slow_print
import random


def afficher_etat(joueur):
    # affiche le nom, la barre de vie et l'expérience du joueur
    print(encadre(f"{colorize(joueur.nom, 'cyan')} :"))
    print(f"  Vie : {barre_de_vie(joueur.vie, joueur.degats)}")
    print(f"  Expérience : {colorize(str(joueur.experience), 'jaune')}")
    print("-" * 40)


def combat():
    input("Appuyez sur [Entrée] pour lancer le prochain tour...")

    jc = Jc()
    florent = Florent()
    joueurs = [jc, florent]
    tour = 0

    slow_print(encadre("🔥 DÉBUT DU COMBAT : Jc le Pilote vs Florent le Développeur 🔥"))

    while jc.degats < jc.vie and florent.degats < florent.vie:
        attaquant = joueurs[tour % 2]
        cible = joueurs[(tour + 1) % 2]
        frappe_indice = random.randint(0, len(attaquant.frappes) - 1)
        frappe_nom = attaquant.frappes[frappe_indice]['nom']
        icone = icone_frappe(frappe_nom)

        slow_print(colorize(f"\n=== Tour {tour + 1} : {attaquant.nom} attaque ===", 'violet'))
        slow_print(f"{colorize(attaquant.nom, 'cyan')} prépare {icone} {frappe_nom}")
        attaquant.frappe(cible, frappe_indice)
        afficher_etat(cible)

        tour += 1

    # annonce du vainqueur du combat entre Jc et Florent
    if jc.degats >= jc.vie:
        winner = florent
    else:
        winner = jc

    slow_print(colorize("\n🏆 VICTOIRE 🏆", 'vert'))
    slow_print(encadre(f"{winner.nom} l'emporte après {tour} tours !"))


if __name__ == "__main__":
    combat()
