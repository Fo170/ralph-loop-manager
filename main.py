#!/usr/bin/env python3
"""Point d'entrée de l'application Ralph Loop Manager."""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QFontDatabase
from gui.main_window import MainWindow


def load_emoji_font():
    """Charge Noto Color Emoji et retourne le nom de la famille."""
    import platform as _platform
    if _platform.system() == "Windows":
        emoji_path = Path("C:/Windows/Fonts/seguiemj.ttf")
    else:
        emoji_path = Path("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
    if not emoji_path.exists():
        print(f"[FONT] Fichier emoji non trouvé: {emoji_path}")
        return None

    font_id = QFontDatabase.addApplicationFont(str(emoji_path))
    if font_id == -1:
        print("[FONT] addApplicationFont a échoué")
        return None

    families = QFontDatabase.applicationFontFamilies(font_id)
    if not families:
        print("[FONT] Aucune famille trouvée")
        return None

    print(f"[FONT] Emoji chargée: {families[0]}")
    return families[0]


def main():
    from core.diagnostic import run as diag_run, show as diag_show
    diag_errors = diag_run()
    if diag_errors:
        diag_show(diag_errors)
        # On continue quand même — la GUI peut être utile pour voir les erreurs

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Charger la police emoji (sera utilisée seulement dans la console)
    emoji_font = load_emoji_font()

    # Police globale : NOTO SANS (texte normal) — pas Noto Color Emoji
    # Noto Color Emoji remplace les chiffres/lettres par des versions emoji
    # On teste si Noto Sans existe en créant un QFont et vérifiant sa famille
    test_font = QFont("Noto Sans", 10)
    if test_font.exactMatch():
        normal_font = test_font
        print("[FONT] Police globale: Noto Sans")
    else:
        normal_font = QFont("DejaVu Sans", 10)
        print("[FONT] Police globale: DejaVu Sans")

    app.setFont(normal_font)

    window = MainWindow(emoji_font=emoji_font)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()