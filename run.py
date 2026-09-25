"""
Script de démarrage unifié pour l'application Générateur de Prompts IA.
Lance le serveur Backend FastAPI et l'interface Frontend Streamlit en parallèle.
Compatible Windows (gestion UTF-8 console).
"""

import sys
import subprocess
import time
from pathlib import Path

# Assurer l'encodage UTF-8 pour la console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).parent


def run():
    print("=" * 70)
    print("[DEMARRAGE] APPLICATION ENTERPRISE AI PROMPT STUDIO")
    print("=" * 70)
    
    python_exec = sys.executable

    print("\n[1/2] Lancement du serveur Backend FastAPI (port 8000)...")
    backend_proc = subprocess.Popen(
        [python_exec, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=str(PROJECT_ROOT)
    )

    print("Attente de l'initialisation du backend...")
    time.sleep(2)

    print("\n[2/2] Lancement de l'interface Frontend Streamlit (port 8501)...")
    frontend_proc = subprocess.Popen(
        [python_exec, "-m", "streamlit", "run", "frontend/app.py", "--server.port", "8501"],
        cwd=str(PROJECT_ROOT)
    )

    print("\n" + "=" * 70)
    print("[INFO] APPLICATION EN COURS D'EXECUTION :")
    print("   - Interface Utilisateur : http://localhost:8501")
    print("   - Documentation Swagger API : http://localhost:8000/docs")
    print("   - Documentation ReDoc API : http://localhost:8000/redoc")
    print("   - Appuyez sur Ctrl+C pour arreter les deux services.")
    print("=" * 70 + "\n")

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print("Le backend s'est arrete.")
                break
            if frontend_proc.poll() is not None:
                print("Le frontend s'est arrete.")
                break
    except KeyboardInterrupt:
        print("\nArret en cours des services...")
    finally:
        if backend_proc.poll() is None:
            backend_proc.terminate()
        if frontend_proc.poll() is None:
            frontend_proc.terminate()
        print("[OK] Services arretes proprement.")


if __name__ == "__main__":
    run()
