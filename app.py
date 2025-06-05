import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Analyse EOLE Avancée", layout="wide")
st.title("Analyse des heures & budgets EOLE")

uploaded_files = st.file_uploader("Importez vos fichiers CSV de pointages", type="csv", accept_multiple_files=True)

if uploaded_files:
    all_data = []

    for file in uploaded_files:
        try:
            df = pd.read_csv(file, sep=';', encoding='latin1', engine='python')
            chantier_col = "LibellÃ© chantier/ss-section"
            nom_col = "Nom du personnel"
            prenom_col = "PrÃ©nom Du personnel"
            heures_col = "Nombre d'heures du type d'heure"
            montant_col = "Montant des heures valorisÃ©s du type d'heure"
            date_col = "Date de pointage"
            gba_col = "Rubrique GBA"
            agence_col = "LibellÃ© agence du personnel"

            df = df[df[chantier_col].astype(str).str.contains("EOLE", case=False, na=False)]

            df["Nom complet"] = df[nom_col].astype(str).str.upper() + " " + df[prenom_col].astype(str).str.upper()
            df["Heures"] = pd.to_numeric(df[heures_col].astype(str).str.replace(",", ".", regex=False), errors="coerce").fillna(0)
            df["Montant"] = pd.to_numeric(df[montant_col].astype(str).str.replace(",", ".", regex=False), errors="coerce").fillna(0)
            df["Date"] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")

            all_data.append(df[["Nom complet", "Heures", "Montant", "Date", gba_col, agence_col]])

        except Exception as e:
            st.error(f"Erreur dans le fichier {file.name} : {e}")

    if all_data:
        df_final = pd.concat(all_data).dropna(subset=["Date"])

        # Filtres avancés
        gba_options = df_final[gba_col].dropna().unique()
        agence_options = df_final[agence_col].dropna().unique()

        selected_gba = st.multiselect("Filtrer par Rubrique GBA :", sorted(gba_options))
        selected_agence = st.multiselect("Filtrer par agence :", sorted(agence_options))

        if selected_gba:
            df_final = df_final[df_final[gba_col].isin(selected_gba)]
        if selected_agence:
            df_final = df_final[df_final[agence_col].isin(selected_agence)]

        # Filtrage par date
        min_date = df_final["Date"].min()
        max_date = df_final["Date"].max()
        date_range = st.date_input("Filtrer par plage de dates", [min_date, max_date])

        if len(date_range) == 2:
            start_date, end_date = date_range
            df_final = df_final[(df_final["Date"] >= pd.to_datetime(start_date)) & (df_final["Date"] <= pd.to_datetime(end_date))]

        # Agrégation
        agg_df = df_final.groupby("Nom complet").agg({"Heures": "sum", "Montant": "sum"}).reset_index()
        agg_df = agg_df.sort_values(by="Heures", ascending=False)

        st.success(f"{len(agg_df)} personnes trouvées entre {start_date.strftime('%d/%m/%Y')} et {end_date.strftime('%d/%m/%Y')}")

        st.dataframe(agg_df.drop(columns=["Montant"]), use_container_width=True)


        st.subheader("Visualisations avancées")

        col1, col2 = st.columns(2)

        # Camembert - Heures par agence
        with col1:
            heures_agence = df_final.groupby(agence_col)["Heures"].sum().reset_index()
            fig1 = px.pie(heures_agence, names=agence_col, values="Heures", title="Répartition des heures par agence")
            st.plotly_chart(fig1, use_container_width=True)

        # Histogramme - Effectif par Rubrique GBA
        with col2:
            effectif_gba = df_final.groupby(gba_col)["Nom complet"].nunique().reset_index(name="Nombre d'agents")
            fig2 = px.bar(effectif_gba, x="Nombre d'agents", y=gba_col, orientation='h',
                          title="Nombre d'agents par Rubrique GBA")
            st.plotly_chart(fig2, use_container_width=True)

        # Courbe temporelle - Heures totales par mois
        df_final["Mois"] = df_final["Date"].dt.to_period("M").astype(str)
        heures_par_mois = df_final.groupby("Mois")["Heures"].sum().reset_index()
        fig3 = px.line(heures_par_mois, x="Mois", y="Heures", markers=True, title="Évolution mensuelle des heures")
        st.plotly_chart(fig3, use_container_width=True)

        # Top 10 agents - Barres horizontales
        top10 = agg_df.head(10)
        fig4 = px.bar(top10, x="Heures", y="Nom complet", orientation='h', title="Top 10 agents par heures")
        st.plotly_chart(fig4, use_container_width=True)

        # Export
        st.download_button("Exporter en CSV", data=agg_df.to_csv(index=False).encode('utf-8'),
                           file_name="bilan_eole.csv", mime="text/csv")

    else:
        st.warning("Aucune donnée exploitable trouvée.")
else:
    st.info(" Importez vos fichiers CSV pour commencer.")
