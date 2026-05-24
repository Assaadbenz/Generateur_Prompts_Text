import streamlit as st
import requests
from typing import List, Dict, Any
import pyperclip

# Configuration de la page
st.set_page_config(
    page_title="Générateur de Prompts",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL de l'API
API_BASE_URL = "http://localhost:8000"


# ============================================================================
# Fonctions utilitaires
# ============================================================================
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
        st.error(f"Erreur API: {response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion: {e}")
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
        else:
            st.error(f"Erreur API: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion: {e}")
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
        else:
            st.error(f"Erreur lors de la sauvegarde: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion: {e}")
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
        return False
    except requests.exceptions.RequestException:
        return False


# ============================================================================
# Interface principale
# ============================================================================
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
                        st.success("Prompt généré! ✓")
            else:
                st.warning("Remplissez l'expertise et la mission")
    
    with col_btn2:
        if st.button("🔧 Optimiser", use_container_width=True):
            if session.generated_prompt:
                with st.spinner("Optimisation en cours..."):
                    result = optimize_prompt(session.generated_prompt)
                    if result:
                        st.info(f"Score initial: {session.quality_score}")
                        if result.get("missing_keywords"):
                            st.warning(f"Mots-clés manquants: {', '.join(result['missing_keywords'])}")
            else:
                st.warning("Générez d'abord un prompt")


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
            titre_save = st.text_input("Titre du prompt", value=f"Prompt {mission[:20]}")
        with col_save2:
            if st.button("💾 Sauvegarder", use_container_width=True):
                if titre_save:
                    save_prompt_to_db(titre_save, session.generated_prompt, session.quality_score)
    else:
        st.info("👈 Remplissez le formulaire et générez un prompt")


# ============================================================================
# Barre latérale: Historique
# ============================================================================
with st.sidebar:
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
                
                col_copy, col_del = st.columns(2)
                with col_copy:
                    if st.button("📋 Copier", key=f"copy_{prompt['id']}", use_container_width=True):
                        copy_to_clipboard(prompt['prompt_text'])
                
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
