"""
Script d'exécution des tests automatisés avec rapport de synthèse.
Compatible Windows (gestion UTF-8 console).
"""

import sys
import subprocess
from pathlib import Path

# Assurer l'encodage UTF-8 pour la console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).parent


def run_tests():
    print("=" * 70)
    print("[TESTS] EXECUTION DE LA SUITE DE TESTS AUTOMATISES (PYTEST)")
    print("=" * 70)

    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("[SUCCES] TOUS LES TESTS ONT REUSSI AVEC SUCCES !")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("[ECHEC] DES TESTS ONT ECHOUE. VEUILLEZ VERIFIER LES LOGS CI-DESSUS.")
        print("=" * 70)

    sys.exit(result.returncode)


if __name__ == "__main__":
    run_tests()
