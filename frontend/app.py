import streamlit as st
import requests
from typing import List, Dict, Any
import pyperclip
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration de la page
st.set_page_config(
    page_title="Générateur de Prompts",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL de l'API - read from environment or use default
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


# ============================================================================
# Fonctions utilitaires
# ============================================================================
def check_api_health():
    """Check if API is running."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/health",
            timeout=5
        )
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def copy_to_clipboard(text: str):
    try:
        pyperclip.copy(text)
        st.toast("✅ Copié !", icon="📋")
    except Exception as e:
        st.toast(f"❌ Erreur: {e}", icon="⚠️")


# Initialiser les variables de session
if 'generated_prompt' not in st.session_state:
    st.session_state.generated_prompt = None
if 'quality_score' not in st.session_state:
    st.session_state.quality_score = None
if 'prompts_offset' not in st.session_state:
    st.session_state.prompts_offset = 0
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'saved_mission' not in st.session_state:
    st.session_state.saved_mission = ""
if 'optimization_result' not in st.session_state:
    st.session_state.optimization_result = None
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False


def fetch_prompts(limit: int = 5, offset: int = 0) -> tuple:
    try:
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
        placeholder="ex: Marketing, Développement, Rédaction...",
        help="Domaine d'expertise du modèle"
    )
    
    mission = st.text_area(
        "Mission",
        placeholder="Décrivez précisément ce que le modèle doit faire...",
        height=100,
        help="La tâche à accomplir"
    )
    
    output_format = st.selectbox(
        "Format de sortie",
        options=["Texte", "Liste", "Tableau", "Code"],
        help="Format attendu pour la réponse"
    )
    
    tone = st.select_slider(
        "Ton",
        options=["Très formel", "Formel", "Neutre", "Décontracté", "Très décontracté"],
        value="Neutre"
    )
    
    length = st.select_slider(
        "Longueur",
        options=["Courte", "Moyenne", "Longue"],
        value="Moyenne"
    )
    
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
                    save_prompt_to_db(titre_save, session.generated_prompt, session.quality_score)
        
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
        --bg-color: #0e1117;
        --secondary-bg: #161b22;
        --text-color: #c9d1d9;
        --border-color: #30363d;
        --input-bg: #0d1117;
    }
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0e1117 !important;
        color: #c9d1d9 !important;
    }
    
    [data-testid="stHeader"] {
        background-color: #0e1117 !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #161b22 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #c9d1d9 !important;
    }
    
    .stTabs [data-testid="stMarkdownContainer"] {
        color: #c9d1d9 !important;
    }
    
    .stTextInput > div > div > input,
    .stTextArea textarea,
    .stSelectbox > div > div > select {
        background-color: #0d1117 !important;
        color: #c9d1d9 !important;
        border-color: #30363d !important;
    }
    
    .stSelectbox > div > div > div,
    .stSelectbox > div > div > input {
        color: #c9d1d9 !important;
    }
    
    [data-testid="stVerticalBlock"] > [style*="flex-direction"] > [data-testid="stVerticalBlock"] {
        background-color: transparent !important;
    }
    
    .stExpander {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
    }
    
    .stExpander [data-testid="stExpanderDetails"] {
        background-color: #0d1117 !important;
    }
    
    .stCode {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
    }
    
    pre {
        background-color: #0d1117 !important;
        color: #c9d1d9 !important;
    }
    
    code {
        background-color: #161b22 !important;
        color: #79c0ff !important;
        border-color: #30363d !important;
    }
    
    .stMetric {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 0.5rem;
        padding: 1rem;
    }
    
    .stMetric > div > div > h3,
    .stMetric > div > div > p {
        color: #c9d1d9 !important;
    }
    
    h1, h2, h3, h4, h5, h6, label, p, span, div {
        color: #c9d1d9 !important;
    }
    
    .stButton > button {
        background-color: #1f6feb !important;
        color: #c9d1d9 !important;
        border: 1px solid #1f6feb !important;
    }
    
    .stButton > button:hover {
        background-color: #388bfd !important;
    }
    
    .stButton > button[data-testid="baseButton-secondary"] {
        background-color: #1f6feb !important;
        border: 1px solid #1f6feb !important;
    }
    
    .stButton > button[data-testid="baseButton-secondary"]:hover {
        background-color: #388bfd !important;
    }
    
    [data-testid="stNotification"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
    }
    
    .streamlit-expanderHeader {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
    }
    
    .streamlit-expanderContent {
        background-color: #0d1117 !important;
    }
    
    [data-testid="stMarkdownContainer"] {
        color: #c9d1d9 !important;
    }
    
    /* Info/Success/Error/Warning boxes */
    [data-testid="stAlert"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
    }
    
    [data-testid="stAlert"] > div {
        color: #c9d1d9 !important;
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
        background-color: #0055ff !important;
        color: #ffffff !important;
        border: 1px solid #0055ff !important;
    }
    
    .stButton > button:hover {
        background-color: #0969da !important;
    }
    
    .stButton > button[data-testid="baseButton-secondary"] {
        background-color: #0055ff !important;
        border: 1px solid #0055ff !important;
    }
    
    .stButton > button[data-testid="baseButton-secondary"]:hover {
        background-color: #0969da !important;
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
