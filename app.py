"""
Application Streamlit – Prédiction du taux de participation aux élections municipales 2032
========================================================================================

Cette application permet de :
- Sélectionner une commune et obtenir sa participation prédite pour 2032
- Visualiser les caractéristiques de la commune (population, chômage, revenu, criminalité)
- Comparer la prédiction avec la moyenne nationale
- Trouver les communes les plus similaires (profil socio-économique)
- Lancer des prédictions en mode batch (fichier CSV)
- Consulter l’historique des prédictions de la session

Modèle : Random Forest entraîné sur les années 2014 et 2026 (2020 exclue).
Données : INSEE, Ministère de l’Intérieur.
"""

import streamlit as st
import pandas as pd
import numpy as np
import pickle
from io import BytesIO
from scipy.spatial.distance import cdist
from sklearn.preprocessing import StandardScaler

# -------------------------------------------------------------------
# 1. Configuration de la page et chargement des données (avec cache)
# -------------------------------------------------------------------
st.set_page_config(page_title="Prédiction municipales 2032", layout="wide")

@st.cache_resource
def load_model():
    """Charge le pipeline entraîné (imputation + normalisation + Random Forest)."""
    with open('model_pipeline.pkl', 'rb') as f:
        return pickle.load(f)

@st.cache_data
def load_features():
    """
    Charge les caractéristiques des communes pour l'année 2026.
    Ces données serviront à faire les prédictions (l'année sera forcée à 2032).
    Le fichier doit contenir au moins : code_commune, population, taux_chomage,
    revenu_median, taux_criminalite. On ajoute le nom de la commune si disponible.
    """
    df = pd.read_csv("features_2026.csv")
    # Ajout des noms de communes (fichier optionnel)
    try:
        noms = pd.read_csv("communes_noms.csv")
        df = df.merge(noms, on='code_commune', how='left')
        df['nom_commune'] = df['nom_commune'].fillna(df['code_commune'])
    except FileNotFoundError:
        df['nom_commune'] = df['code_commune']
    return df

# Chargement des objets
pipeline = load_model()
df_2026 = load_features()

# -------------------------------------------------------------------
# 2. Pré‑calcul des prédictions pour toutes les communes (caché)
# -------------------------------------------------------------------
@st.cache_data
def compute_all_predictions(df):
    """
    Calcule le taux de participation prédit pour chaque commune (année forcée à 2032).
    Retourne le DataFrame avec une colonne 'taux_2032_pred'.
    """
    features = ['annee', 'population', 'taux_chomage', 'revenu_median', 'taux_criminalite']
    X_all = df[features].copy()
    X_all['annee'] = 2032
    preds = pipeline.predict(X_all)
    df_result = df.copy()
    df_result['taux_2032_pred'] = preds
    return df_result

df_2026 = compute_all_predictions(df_2026)

# Statistiques nationales
moyenne_nat = df_2026['taux_2032_pred'].mean()
ecart_nat = df_2026['taux_2032_pred'].std()
# MAE typique du modèle (issue de l’entraînement)
MAE_MODELE = 3.05

# -------------------------------------------------------------------
# 3. Interface utilisateur principale
# -------------------------------------------------------------------
st.title("🗳️ Prédiction du taux de participation – Municipales 2032")
st.markdown("L'application estime le taux de participation pour chaque commune française en 2032 à partir de ses caractéristiques socio‑économiques (population, chômage, revenu, criminalité).")

# Barre latérale : options globales
with st.sidebar:
    st.header("⚙️ Options")
    show_similar = st.checkbox("Afficher les communes similaires", value=True)
    batch_mode = st.checkbox("Mode batch (prédictions multiples)", value=False)

# Sélection de la commune
commune_options = df_2026.sort_values('nom_commune')['nom_commune'].tolist()
selected_name = st.selectbox("Choisissez une commune", commune_options)
selected = df_2026[df_2026['nom_commune'] == selected_name].iloc[0]

# -------------------------------------------------------------------
# 4. Affichage des caractéristiques de la commune sélectionnée
# -------------------------------------------------------------------
st.subheader("📋 Caractéristiques de la commune")
col1, col2 = st.columns(2)
with col1:
    st.metric("Population", f"{selected['population']:,.0f}")
    st.metric("Taux de chômage", f"{selected['taux_chomage']:.1f} %")
with col2:
    st.metric("Revenu médian", f"{selected['revenu_median']:,.0f} €")
    st.metric("Taux de criminalité", f"{selected['taux_criminalite']:.1f} (pour 1000 hab.)")

# -------------------------------------------------------------------
# 5. Prédiction proprement dite
# -------------------------------------------------------------------
if st.button("🔮 Prédire le taux de participation", type="primary"):
    # Construire un DataFrame d’entrée avec les features
    features = ['annee', 'population', 'taux_chomage', 'revenu_median', 'taux_criminalite']
    X_new = pd.DataFrame([[
        2032,
        selected['population'],
        selected['taux_chomage'],
        selected['revenu_median'],
        selected['taux_criminalite']
    ]], columns=features)
    
    pred = pipeline.predict(X_new)[0]
    borne_inf = pred - MAE_MODELE
    borne_sup = pred + MAE_MODELE
    
    st.success(f"## 📈 Taux de participation prédit : **{pred:.1f} %**")
    st.caption(f"Intervalle de confiance approximatif : [{borne_inf:.1f} % – {borne_sup:.1f} %]")
    
    # Comparaison avec la moyenne nationale
    diff = pred - moyenne_nat
    if diff > 0:
        st.info(f"ℹ️ Ce taux est **+{diff:.1f} points** au‑dessus de la moyenne nationale ({moyenne_nat:.1f} %).")
    else:
        st.info(f"ℹ️ Ce taux est **{diff:.1f} points** en dessous de la moyenne nationale ({moyenne_nat:.1f} %).")
    
    # Barre de progression pour visualiser le rang
    st.progress(min(int((pred - 20) / 60 * 100), 100) if 20 <= pred <= 80 else 50)
    
    # Historique de session
    if 'history' not in st.session_state:
        st.session_state.history = []
    st.session_state.history.append((selected_name, pred))
    st.caption("✅ Prédiction enregistrée dans l'historique de la session.")

# -------------------------------------------------------------------
# 6. Communes similaires (profil socio‑économique proche)
# -------------------------------------------------------------------
if show_similar:
    st.subheader("🔍 Communes au profil socio‑économique proche")
    # Normalisation des features numériques pour calcul de distance euclidienne
    features_num = ['population', 'taux_chomage', 'revenu_median', 'taux_criminalite']
    scaler = StandardScaler()
    X_all_scaled = scaler.fit_transform(df_2026[features_num])
    X_sel_scaled = scaler.transform([selected[features_num].values])
    distances = cdist(X_sel_scaled, X_all_scaled, metric='euclidean')[0]
    df_2026['distance'] = distances
    similar = df_2026[df_2026['code_commune'] != selected['code_commune']].nsmallest(5, 'distance')
    st.dataframe(similar[['nom_commune', 'taux_2032_pred', 'population', 'taux_chomage']].rename(
        columns={'taux_2032_pred': 'Taux prédit (%)'}))

# -------------------------------------------------------------------
# 7. Mode batch : prédiction pour une liste de communes (fichier CSV)
# -------------------------------------------------------------------
if batch_mode:
    st.subheader("📂 Mode batch – prédictions multiples")
    uploaded = st.file_uploader("Téléchargez un fichier CSV avec une colonne 'code_commune'", type="csv")
    if uploaded is not None:
        codes_df = pd.read_csv(uploaded)
        if 'code_commune' in codes_df.columns:
            merged = codes_df.merge(df_2026[['code_commune', 'taux_2032_pred', 'nom_commune']],
                                    on='code_commune', how='left')
            st.dataframe(merged)
            csv_output = merged.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Télécharger les prédictions", data=csv_output,
                               file_name="predictions_batch.csv", mime="text/csv")
        else:
            st.error("Le fichier CSV doit contenir une colonne 'code_commune'.")

# -------------------------------------------------------------------
# 8. Historique des prédictions de la session
# -------------------------------------------------------------------
if st.checkbox("📜 Afficher l'historique des prédictions (session actuelle)"):
    if 'history' in st.session_state and st.session_state.history:
        hist_df = pd.DataFrame(st.session_state.history, columns=["Commune", "Taux prédit (%)"])
        st.table(hist_df)
    else:
        st.info("Aucune prédiction effectuée dans cette session.")

# -------------------------------------------------------------------
# 9. Pied de page (informations techniques)
# -------------------------------------------------------------------
st.markdown("---")
st.caption(f"Modèle : Random Forest (MAE = {MAE_MODELE:.2f} points, R² ≈ 0.88) | "
           f"Données : INSEE, Ministère de l'Intérieur | Année de référence : 2026 → 2032.")