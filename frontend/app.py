# ============================================================================
# INTERFACE UTILISATEUR - GÉNÉRATEUR DE PROMPTS (STREAMLIT)
# ============================================================================
# Ce fichier crée l'interface web avec Streamlit
# Streamlit permet de créer rapidement une app web sans HTML/CSS/JavaScript
# L'app se connecte à l'API FastAPI pour générer et optimiser les prompts

# Imports nécessaires
import streamlit as st  # Framework pour l'interface web
import requests  # Pour faire des appels à l'API
from typing import List, Dict, Any  # Types pour les annotations
import pyperclip  # Pour copier du texte dans le presse-papiers
import os  # Pour accéder aux variables d'environnement
import json  # Pour traiter les données JSON
from dotenv import load_dotenv  # Pour charger les variables d'environnement du fichier .env

# Charger les variables d'environnement depuis le fichier .env
# Cela permet de stocker les informations sensibles (URLs, clés, etc.)
load_dotenv()

# ============================================================================
# CONFIGURATION STREAMLIT
# ============================================================================
# st.set_page_config() configure l'apparence générale de l'app
st.set_page_config(
    page_title="Générateur de Prompts",  # Titre dans l'onglet du navigateur
    page_icon="✨",  # Icône dans l'onglet du navigateur
    layout="wide",  # Utiliser la largeur complète de l'écran
    initial_sidebar_state="expanded"  # Afficher la barre latérale par défaut
)

# URL de l'API - lire depuis l'environnement ou utiliser par défaut
# Cela permet de changer l'URL sans modifier le code
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def check_api_health():
    """Vérifie si l'API est en ligne et fonctionnelle.
    
    Retourne: True si l'API répond, False sinon
    
    Utilisation: Cette fonction est appelée au démarrage pour afficher
    une alerte si l'API n'est pas disponible.
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/health",  # Endpoint de vérification de l'API
            timeout=5  # Attendre maximum 5 secondes
        )
        return response.status_code == 200  # 200 = succès
    except requests.exceptions.RequestException:
        # Si la requête échoue (connexion refusée, timeout, etc.)
        return False


def copy_to_clipboard(text: str):
    """Copie du texte dans le presse-papiers et affiche une notification.
    
    Paramètres:
    - text: le texte à copier
    
    Cette fonction utilise pyperclip pour copier le texte,
    puis affiche un message de confirmation avec st.toast()
    """
    try:
        pyperclip.copy(text)  # Copier le texte
        st.toast("✅ Copié !", icon="📋")  # Afficher une notification de succès
    except Exception as e:
        st.toast(f"❌ Erreur: {e}", icon="⚠️")  # Afficher un message d'erreur


# ============================================================================
# INITIALISATION DES VARIABLES DE SESSION
# ============================================================================
# st.session_state permet de stocker des données qui persistent
# quand l'utilisateur interagit avec la page (sans recharger)
# C'est comme des variables "mémoire" pour chaque session utilisateur

if 'generated_prompt' not in st.session_state:
    st.session_state.generated_prompt = None  # Le prompt généré récemment
if 'quality_score' not in st.session_state:
    st.session_state.quality_score = None  # Score du prompt généré
if 'prompts_offset' not in st.session_state:
    st.session_state.prompts_offset = 0  # Pagination des prompts sauvegardés
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""  # Termes de recherche
if 'saved_mission' not in st.session_state:
    st.session_state.saved_mission = ""  # Dernière mission sauvegardée
if 'optimization_result' not in st.session_state:
    st.session_state.optimization_result = None  # Résultat de l'optimisation
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False  # Mode sombre activé ou pas
if 'form_expertise' not in st.session_state:
    st.session_state.form_expertise = ""  # Champ expertise du formulaire
if 'form_mission' not in st.session_state:
    st.session_state.form_mission = ""  # Champ mission du formulaire
if 'form_tone' not in st.session_state:
    st.session_state.form_tone = "Neutre"  # Ton par défaut
if 'form_format' not in st.session_state:
    st.session_state.form_format = "Texte"  # Format par défaut
if 'form_length' not in st.session_state:
    st.session_state.form_length = "Moyenne"  # Longueur par défaut


def fetch_prompts(limit: int = 5, offset: int = 0) -> tuple:
    """Récupère une liste de prompts sauvegardés depuis l'API.
    
    Paramètres:
    - limit: nombre de prompts à récupérer (par défaut 5)
    - offset: nombre de prompts à sauter (pour la pagination)
    
    Retourne: tuple contenant (prompts, total, limit, offset)
    - prompts: liste des prompts récupérés
    - total: nombre total de prompts en base de données
    """
    try:
        # Faire une requête GET à l'API pour récupérer les prompts
        response = requests.get(
            f"{API_BASE_URL}/prompts",
            params={"limit": limit, "offset": offset},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("prompts", []), data.get("total", 0), data.get("limit", limit), data.get("offset", offset)
        st.error(f"Erreur API ({response.status_code})")
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion à l'API: {e}")
    return [], 0, limit, offset


def search_prompts_api(query: str, limit: int = 5, offset: int = 0) -> tuple:
    """Recherche des prompts qui contiennent la query."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/prompts/search",
            params={"q": query, "limit": limit, "offset": offset},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("prompts", []), data.get("total", 0), data.get("limit", limit), data.get("offset", offset)
        st.error(f"Erreur API ({response.status_code})")
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion: {e}")
    return [], 0, limit, offset


def generate_prompt(expertise: str, mission: str, tone: str, output_format: str, length: str) -> Dict[str, Any]:
    try:
        payload = {
            "expertise": expertise,
            "mission": mission,
            "tone": tone,
            "output_format": output_format,
            "length": length
        }
        response = requests.post(
            f"{API_BASE_URL}/generate",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 422:
            error_details = response.json().get("detail", "Erreur de validation")
            st.error(f"❌ Erreur de validation: {error_details}")
            return None
        else:
            st.error(f"❌ Erreur API: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.Timeout:
        st.error("❌ Timeout: L'API met trop de temps à répondre")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Erreur de connexion: Impossible de se connecter à {API_BASE_URL}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur de connexion: {e}")
        return None


def optimize_prompt(prompt_text: str) -> Dict[str, Any]:
    """Optimise un prompt via l'API."""
    try:
        payload = {"prompt_text": prompt_text}
        response = requests.post(
            f"{API_BASE_URL}/optimize",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 422:
            error_details = response.json().get("detail", "Erreur de validation")
            st.error(f"❌ Erreur de validation: {error_details}")
            return None
        else:
            st.error(f"❌ Erreur API: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        st.error("❌ Timeout: L'API met trop de temps à répondre")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Erreur de connexion: Impossible de se connecter à {API_BASE_URL}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur de connexion: {e}")
        return None


def save_prompt_to_db(titre: str, prompt_text: str, score: int) -> bool:
    """Sauvegarde un prompt dans la base de données."""
    try:
        payload = {
            "titre": titre,
            "prompt_text": prompt_text,
            "score": score
        }
        response = requests.post(
            f"{API_BASE_URL}/prompts/save",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            st.success("Prompt sauvegardé avec succès! ✓")
            return True
        elif response.status_code == 422:
            error_details = response.json().get("detail", "Erreur de validation")
            st.error(f"❌ Erreur de validation: {error_details}")
            return False
        else:
            st.error(f"❌ Erreur lors de la sauvegarde: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        st.error("❌ Timeout: L'API met trop de temps à répondre")
        return False
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Erreur de connexion: Impossible de se connecter à {API_BASE_URL}")
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur de connexion: {e}")
        return False


def delete_prompt_from_db(prompt_id: int) -> bool:
    """Supprime un prompt de la base de données."""
    try:
        response = requests.delete(
            f"{API_BASE_URL}/prompts/{prompt_id}",
            timeout=10
        )
        if response.status_code == 200:
            return True
        st.error(f"Erreur lors de la suppression ({response.status_code})")
        return False
    except requests.exceptions.RequestException:
        st.error("Erreur de connexion lors de la suppression")
        return False


def download_json(prompt_id: int = None) -> bytes:
    """Télécharge les prompts en JSON."""
    try:
        params = {}
        if prompt_id:
            params["prompt_id"] = prompt_id
        
        response = requests.get(
            f"{API_BASE_URL}/export/json",
            params=params,
            timeout=10
        )
        if response.status_code == 200:
            return response.content
        st.error(f"Erreur lors de l'export JSON ({response.status_code})")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion: {e}")
        return None


def download_markdown(prompt_id: int = None) -> bytes:
    """Télécharge les prompts en Markdown."""
    try:
        params = {}
        if prompt_id:
            params["prompt_id"] = prompt_id
        
        response = requests.get(
            f"{API_BASE_URL}/export/markdown",
            params=params,
            timeout=10
        )
        if response.status_code == 200:
            return response.content
        st.error(f"Erreur lors de l'export Markdown ({response.status_code})")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion: {e}")
        return None


# ============================================================================
# Interface principale
# ============================================================================
# Check API health on startup
if not check_api_health():
    st.error(f"""
    ❌ **Impossible de se connecter à l'API**
    
    Assurez-vous que:
    1. L'API FastAPI est en cours d'exécution: `python -m uvicorn backend.main:app --reload`
    2. L'URL de l'API est correcte: {API_BASE_URL}
    3. Vérifiez le fichier `.env` pour API_BASE_URL
    """)
    st.stop()

st.title("✨ Générateur et Optimiseur de Prompts")
st.markdown("Créez et optimisez des prompts de qualité pour vos modèles IA")

session = st.session_state

# Créer deux colonnes
col_form, col_result = st.columns([1, 1], gap="medium")

# ============================================================================
# Colonne gauche: Formulaire
# ============================================================================
with col_form:
    st.subheader("📝 Formulaire")
    
    expertise = st.text_input(
        "Expertise",
        value=session.form_expertise,
        placeholder="ex: Marketing, Développement, Rédaction...",
        help="Domaine d'expertise du modèle",
        key="expertise_input"
    )
    session.form_expertise = expertise
    
    mission = st.text_area(
        "Mission",
        value=session.form_mission,
        placeholder="Décrivez précisément ce que le modèle doit faire...",
        height=100,
        help="La tâche à accomplir",
        key="mission_input"
    )
    session.form_mission = mission
    
    output_format = st.selectbox(
        "Format de sortie",
        options=["Texte", "Liste", "Tableau", "Code"],
        index=["Texte", "Liste", "Tableau", "Code"].index(session.form_format),
        help="Format attendu pour la réponse",
        key="format_input"
    )
    session.form_format = output_format
    
    tone = st.select_slider(
        "Ton",
        options=["Très formel", "Formel", "Neutre", "Décontracté", "Très décontracté"],
        value=session.form_tone,
        key="tone_input"
    )
    session.form_tone = tone
    
    length = st.select_slider(
        "Longueur",
        options=["Courte", "Moyenne", "Longue"],
        value=session.form_length,
        key="length_input"
    )
    session.form_length = length
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("🚀 Générer", use_container_width=True, type="primary"):
            if expertise and mission:
                with st.spinner("Génération en cours..."):
                    result = generate_prompt(expertise, mission, tone, output_format, length)
                    if result:
                        session.generated_prompt = result.get("prompt_text")
                        session.quality_score = result.get("score")
                        session.saved_mission = mission
                        session.optimization_result = None
                        st.success("Prompt généré! ✓")
            else:
                st.warning("Remplissez l'expertise et la mission")
    
    with col_btn2:
        if st.button("🔧 Optimiser", use_container_width=True):
            if session.generated_prompt:
                with st.spinner("Optimisation en cours..."):
                    result = optimize_prompt(session.generated_prompt)
                    if result:
                        session.quality_score = result.get("score")
                        session.optimization_result = result
                        st.toast("✅ Optimisation terminée", icon="🔧")
            else:
                st.warning("Générez d'abord un prompt")
    
    # Suggestions d'optimisation sous le bouton
    if session.optimization_result:
        st.markdown("---")
        st.markdown("### 🔧 Suggestions d'optimisation")
        for s in session.optimization_result.get("suggestions", []):
            st.markdown(f"- {s}")
        st.caption(f"Score : {session.optimization_result.get('score', session.quality_score)}/100")


# ============================================================================
# Colonne droite: Résultat
# ============================================================================
with col_result:
    st.subheader("📊 Résultat")
    
    if session.generated_prompt:
        # Affichage du prompt
        st.markdown("### Prompt généré")
        st.code(session.generated_prompt, language="text")
        
        # Barre de score
        if session.quality_score is not None:
            st.markdown("### Score de qualité")
            st.progress(session.quality_score / 100)
            st.metric("Score", f"{session.quality_score}/100")
        
        # Bouton pour sauvegarder
        col_save1, col_save2 = st.columns(2)
        with col_save1:
            titre_save = st.text_input("Titre du prompt", value=f"Prompt {session.saved_mission[:20]}", key="titre_save")
        with col_save2:
            if st.button("💾 Sauvegarder", use_container_width=True):
                if titre_save:
                    if save_prompt_to_db(titre_save, session.generated_prompt, session.quality_score):
                        # Reinitialiser completement le formulaire et les resultats
                        session.generated_prompt = None
                        session.quality_score = None
                        session.optimization_result = None
                        session.form_expertise = ""
                        session.form_mission = ""
                        session.form_tone = "Neutre"
                        session.form_format = "Texte"
                        session.form_length = "Moyenne"
                        st.success("Prompt sauvegarde! Tous les champs ont ete effaces.")
                        st.rerun()
        
        # Boutons d'export
        st.markdown("---")
        st.markdown("### 📥 Exporter")
        col_export1, col_export2, col_export3 = st.columns(3)
        
        with col_export1:
            if st.button("📄 JSON", use_container_width=True, help="Exporter en JSON"):
                json_data = download_json()
                if json_data:
                    st.download_button(
                        label="💾 Télécharger JSON",
                        data=json_data,
                        file_name="prompt.json",
                        mime="application/json",
                        use_container_width=True
                    )
        
        with col_export2:
            if st.button("📝 Markdown", use_container_width=True, help="Exporter en Markdown"):
                md_data = download_markdown()
                if md_data:
                    st.download_button(
                        label="💾 Télécharger MD",
                        data=md_data,
                        file_name="prompt.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
        
        with col_export3:
            if st.button("📚 Tous", use_container_width=True, help="Exporter toute la bibliothèque"):
                json_data = download_json()
                if json_data:
                    st.download_button(
                        label="💾 Tous (JSON)",
                        data=json_data,
                        file_name="prompts_all.json",
                        mime="application/json",
                        use_container_width=True
                    )
    else:
        st.info("👈 Remplissez le formulaire et générez un prompt")


# ============================================================================
# Apply global theme CSS
# ============================================================================
if st.session_state.dark_mode:
    dark_css = """
    <style>
    :root {
        --bg-color: #0a0e27;
        --secondary-bg: #1a1f3a;
        --tertiary-bg: #2a2f4a;
        --text-color: #e0e6f6;
        --text-muted: #a0a8c0;
        --border-color: #3a4060;
        --input-bg: #12172d;
        --accent-blue: #5BB3E8;
        --accent-blue-hover: #7EC8F0;
    }
    
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%) !important;
        color: #e0e6f6 !important;
    }
    
    [data-testid="stHeader"] {
        background-color: rgba(10, 14, 39, 0.8) !important;
        border-bottom: 1px solid #3a4060 !important;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f3a 0%, #2a2f4a 100%) !important;
        border-right: 1px solid #3a4060 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #e0e6f6 !important;
    }
    
    .stTabs [data-testid="stMarkdownContainer"] {
        color: #e0e6f6 !important;
    }
    
    .stTextInput > div > div > input,
    .stTextArea textarea,
    .stSelectbox > div > div > select {
        background-color: #12172d !important;
        color: #e0e6f6 !important;
        border: 1.5px solid #3a4060 !important;
        border-radius: 6px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #5BB3E8 !important;
        box-shadow: 0 0 0 3px rgba(91, 179, 232, 0.1) !important;
    }
    
    .stSelectbox > div > div > div,
    .stSelectbox > div > div > input {
        color: #e0e6f6 !important;
    }
    
    [data-testid="stVerticalBlock"] > [style*="flex-direction"] > [data-testid="stVerticalBlock"] {
        background-color: transparent !important;
    }
    
    .stExpander {
        background-color: #1a1f3a !important;
        border: 1.5px solid #3a4060 !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    
    .stExpander [data-testid="stExpanderDetails"] {
        background-color: #12172d !important;
    }
    
    .stCode {
        background-color: #12172d !important;
        border: 1.5px solid #3a4060 !important;
        border-radius: 8px !important;
    }
    
    pre {
        background-color: #12172d !important;
        color: #e0e6f6 !important;
        border-radius: 6px !important;
        padding: 1rem !important;
    }
    
    code {
        background-color: #1a1f3a !important;
        color: #7EC8F0 !important;
        border-color: #3a4060 !important;
        border-radius: 4px !important;
    }
    
    .stMetric {
        background: linear-gradient(135deg, #1a1f3a 0%, #2a2f4a 100%) !important;
        border: 1.5px solid #3a4060 !important;
        border-radius: 8px !important;
        padding: 1.2rem !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
    }
    
    .stMetric > div > div > h3,
    .stMetric > div > div > p {
        color: #e0e6f6 !important;
    }
    
    h1 {
        color: #e0e6f6 !important;
        font-weight: 700 !important;
    }
    
    h2, h3, h4, h5, h6 {
        color: #e0e6f6 !important;
        font-weight: 600 !important;
    }
    
    label, p, span {
        color: #e0e6f6 !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #5BB3E8 0%, #4A9FD8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(91, 179, 232, 0.25) !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #7EC8F0 0%, #5BB3E8 100%) !important;
        box-shadow: 0 6px 20px rgba(91, 179, 232, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    .stButton > button[data-testid="baseButton-secondary"] {
        background: linear-gradient(135deg, #5BB3E8 0%, #4A9FD8 100%) !important;
        border: none !important;
    }
    
    .stButton > button[data-testid="baseButton-secondary"]:hover {
        background: linear-gradient(135deg, #7EC8F0 0%, #5BB3E8 100%) !important;
        box-shadow: 0 6px 20px rgba(91, 179, 232, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    [data-testid="stNotification"] {
        background-color: #1a1f3a !important;
        border: 1.5px solid #3a4060 !important;
        border-radius: 8px !important;
    }
    
    .streamlit-expanderHeader {
        background-color: #1a1f3a !important;
        border: none !important;
    }
    
    .streamlit-expanderContent {
        background-color: #12172d !important;
    }
    
    [data-testid="stMarkdownContainer"] {
        color: #e0e6f6 !important;
    }
    
    /* Info/Success/Error/Warning boxes */
    [data-testid="stAlert"] {
        background: linear-gradient(135deg, #1a1f3a 0%, #2a2f4a 100%) !important;
        border: 1.5px solid #3a4060 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
    }
    
    [data-testid="stAlert"] > div {
        color: #e0e6f6 !important;
    }
    
    /* Column separators and dividers */
    hr {
        border-color: #3a4060 !important;
        opacity: 0.5 !important;
    }
    
    /* Progress bars */
    .stProgress > div > div {
        background-color: #5BB3E8 !important;
    }
    </style>
    """
    st.markdown(dark_css, unsafe_allow_html=True)
else:
    light_css = """
    <style>
    :root {
        --bg-color: #ffffff;
        --secondary-bg: #f0f2f6;
        --text-color: #262730;
        --border-color: #d9d9e3;
        --input-bg: #ffffff;
    }
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
        color: #262730 !important;
    }
    
    [data-testid="stHeader"] {
        background-color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #f0f2f6 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #262730 !important;
    }
    
    .stTabs [data-testid="stMarkdownContainer"] {
        color: #262730 !important;
    }
    
    .stTextInput > div > div > input,
    .stTextArea textarea,
    .stSelectbox > div > div > select {
        background-color: #ffffff !important;
        color: #262730 !important;
        border-color: #d9d9e3 !important;
    }
    
    .stSelectbox > div > div > div,
    .stSelectbox > div > div > input {
        color: #262730 !important;
    }
    
    .stExpander {
        background-color: #f0f2f6 !important;
        border: 1px solid #d9d9e3 !important;
    }
    
    .stExpander [data-testid="stExpanderDetails"] {
        background-color: #ffffff !important;
    }
    
    .stCode {
        background-color: #f0f2f6 !important;
        border: 1px solid #d9d9e3 !important;
    }
    
    pre {
        background-color: #f0f2f6 !important;
        color: #262730 !important;
    }
    
    code {
        background-color: #f0f2f6 !important;
        color: #0055ff !important;
        border-color: #d9d9e3 !important;
    }
    
    .stMetric {
        background-color: #f0f2f6 !important;
        border: 1px solid #d9d9e3 !important;
        border-radius: 0.5rem;
        padding: 1rem;
    }
    
    .stMetric > div > div > h3,
    .stMetric > div > div > p {
        color: #262730 !important;
    }
    
    h1, h2, h3, h4, h5, h6, label, p, span, div {
        color: #262730 !important;
    }
    
    .stButton > button {
        background-color: #5BB3E8 !important;
        color: #ffffff !important;
        border: 1px solid #5BB3E8 !important;
    }
    
    .stButton > button:hover {
        background-color: #7EC8F0 !important;
    }
    
    .stButton > button[data-testid="baseButton-secondary"] {
        background-color: #5BB3E8 !important;
        border: 1px solid #5BB3E8 !important;
    }
    
    .stButton > button[data-testid="baseButton-secondary"]:hover {
        background-color: #7EC8F0 !important;
    }
    
    [data-testid="stNotification"] {
        background-color: #f0f2f6 !important;
        border: 1px solid #d9d9e3 !important;
    }
    
    .streamlit-expanderHeader {
        background-color: #f0f2f6 !important;
        border: 1px solid #d9d9e3 !important;
    }
    
    .streamlit-expanderContent {
        background-color: #ffffff !important;
    }
    
    [data-testid="stMarkdownContainer"] {
        color: #262730 !important;
    }
    
    /* Info/Success/Error/Warning boxes */
    [data-testid="stAlert"] {
        background-color: #f0f2f6 !important;
        border: 1px solid #d9d9e3 !important;
    }
    
    [data-testid="stAlert"] > div {
        color: #262730 !important;
    }
    </style>
    """
    st.markdown(light_css, unsafe_allow_html=True)

# ============================================================================
# Barre latérale: Historique
# ============================================================================
with st.sidebar:
    # Theme toggle
    col_theme1, col_theme2 = st.columns([3, 1])
    with col_theme1:
        st.markdown("### 🎨 Thème")
    with col_theme2:
        if st.button("☀️" if st.session_state.dark_mode else "🌙", key="theme_toggle"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    
    st.markdown("---")
    st.subheader("📚 Historique")
    
    search_query = st.text_input("🔍 Rechercher", placeholder="Titre ou contenu...", value=session.search_query)
    if search_query != session.search_query:
        session.search_query = search_query
        session.prompts_offset = 0
        st.rerun()
    
    with st.spinner("Chargement..."):
        if session.search_query:
            prompts, total, limit, offset = search_prompts_api(
                query=session.search_query, limit=5, offset=session.prompts_offset
            )
        else:
            prompts, total, limit, offset = fetch_prompts(
                limit=5, offset=session.prompts_offset
            )
    
    st.markdown(f"*{total} prompt(s) au total*")
    
    if prompts:
        for prompt in prompts:
            with st.expander(
                f"📌 {prompt['titre']} (Score: {prompt['score']}/100)",
                expanded=False
            ):
                st.write(f"**Catégorie:** {prompt['categorie']}")
                st.write(f"**Score:** {prompt['score']}/100")
                st.text_area("Prompt", value=prompt['prompt_text'], height=100, disabled=True, key=f"ta_{prompt['id']}")
                
                col_copy, col_export, col_del = st.columns(3)
                with col_copy:
                    if st.button("📋 Copier", key=f"copy_{prompt['id']}", use_container_width=True):
                        copy_to_clipboard(prompt['prompt_text'])
                
                with col_export:
                    json_data = download_json(prompt['id'])
                    if json_data:
                        st.download_button(
                            label="📄 JSON",
                            data=json_data,
                            file_name=f"prompt_{prompt['id']}.json",
                            mime="application/json",
                            key=f"export_json_{prompt['id']}",
                            use_container_width=True
                        )
                
                with col_del:
                    if st.button("🗑️ Supprimer", key=f"delete_{prompt['id']}", use_container_width=True):
                        if delete_prompt_from_db(prompt['id']):
                            session.prompts_offset = 0
                            st.rerun()
        
        col_prev, col_next = st.columns(2)
        with col_prev:
            if offset > 0:
                if st.button("⬅️ Précédent", use_container_width=True):
                    session.prompts_offset = max(0, offset - limit)
                    st.rerun()
        with col_next:
            if offset + limit < total:
                if st.button("Suivant ➡️", use_container_width=True):
                    session.prompts_offset = offset + limit
                    st.rerun()
    else:
        st.info("Aucun prompt sauvegardé")
    
    st.markdown("---")
    st.markdown("*Générateur de Prompts v1.0*")


# ============================================================================
# Footer
# ============================================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center'><small>Alimenté par FastAPI et Streamlit</small></div>",
    unsafe_allow_html=True
)
