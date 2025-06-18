import streamlit as st
import pandas as pd
import io
from datetime import datetime
import traceback

# Configuration de la page
st.set_page_config(
    page_title="Vérificateur de fichiers Excel",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ✅ Configuration des colonnes obligatoires
COLONNES_REFERENTIEL = [
    "STATUTARTICLE", "DTR/NDTR", "CODECOLOR", "LIBCOLORFR", "LIBCOLOREN", "REFCOL", "REFCOLCLIENT", "IFLS", "EAN",
    "NBREF", "NBREFCO", "LIGNEDEPRODUIT", "TYPEPIECE/DIMENSION", "PACKAGING/MERCH", "COMPOSITION", "RECONDUIT/NOUVEAU",
    "IDB", "LIBZONEIMPLANTNAT", "COMMENTAIRESASSISTANT", "CODEIMPLANTNAT", "TYPODEMISAISON1", "TYPODEMISAISON2",
    "NBMAGDEMISAISON1", "NBMAGDEMISAISON2", "DEBUTVIE1", "FINVIE1", "DEBUTVIE2", "FINVIE2", "REFFRN", "LIBFRN",
    "CODEFRN", "BUREAUGS", "ORIGINEPRODUIT", "CODEREGROUPEMENT", "LIBREGROUPEMENT", "PABRUT", "DEVISE", "INCOTERM",
    "CYCFS", "TAUX$", "COEFAPPROCHE", "TXREMISESGLOGALES", "PCLSANSTAXE", "ROYALTIES", "TAXEDEEE", "NOMCP",
    "TAXEECO", "TAXEBOIS", "PCMFDR", "PVFORTTTCFDR", "TXMARGEIN", "ROYALTIESPROMO", "PCMPROMO", "PVPROMO",
    "NUMPACKING", "FLUXIMPLANT", "FLUXREASSORT", "FLUXPROMO", "NBREUNITESPARLOT", "CODECLIENT", "PVUNITAIRE",
    "PRESENCECATALOGUE", "PRESENCEPICKING", "RECAPTAILLES", "GRILLETAILLE"
] + [f"TAILLE{i}" for i in range(1, 40)] + [
    "COLLECTIONPSS", "PCBIMPLANT", "PCBPROMO", "PCBMASTERPICKING", "SPCBINNERPICKING", "CODEPACKINGIMPLANT",
    "CODEPACKINGREASSORT", "DATEOKBUYER", "DATEMAA", "CIRCUITDACHAT", "CODEBCOLL", "DATERELECTUREPSS",
    "CODEGFAMNAT", "LIBGFAMNAT", "VOLUMEIMPLANT", "CODEFAMNAT", "VOLUMEPICKING", "LIBFAMNAT", "CODESFAMNAT",
    "LIBSFAMNAT", "VOLUMEPROMO", "VOLUMETOTAL", "CODESFAMINT", "NUMBOX", "CODEPSS", "LIBPRODUITFR", "LIBPRODUITEN",
    "LIBELLECOURTPRODUITFR", "LIBELLECAISSEPRODUITFR", "CIBLE", "SAISON", "QUADRYPTIQUE", "MARQUE",
    "TEX RESPONSABLE", "PERSONNAGE", "FRANCHISE"
]

COLONNES_PROMO = [
    "STATUTARTICLE", "COMMENTAIRE", "REFCOL", "CLIENT", "NOMCATA", "CPRO", "GRFAMILLE", "NUMEROCATA",
    "DEBUTCATA", "FINCATA", "NUMDISPLAY", "LIGNEDEPRODUIT", "CODEPSS", "LIBPRODUITFR", "MARQUE", "COLORIS",
    "COLORISPSS", "PVFORTTTCFDR", "LIBELLEUB", "NUMPAGEDEf", "NUMUBDEF", "EANMAITRE", "LIBELLEPUB", "LOGO",
    "LEGENDE", "EXISTEAUSSI", "PLUSPRODUIT", "MISEENPAGE", "UNITEDEVENTE", "TYPODEMISAISON1", "TYPODEMISAISON2",
    "PCBPROMO", "PCBMASTERPICKING", "SPCBINNERPICKING", "RECONDUIT/NOUVEAU", "TOPUB", "PHARE", "MECACATA1",
    "MAXXING", "PHOTOCATA1", "MEA_CATA", "VITESSECATA1", "POSCATA1", "REMISEPROMO", "PCMCATA1", "PVCATA1",
    "PVPROMOASAISIR", "TXREMISECATA1", "MARGECATAVAL", "MARGECATA%", "QTEESTOTALES", "VALEURVENTECATA",
    "ESTITXREVENTECATA1", "ESTIVOLUMEVENTECATA1", "ESTICACATA1", "RECEPTIONECH"
]

COLONNES_NUMERIQUES = ["PCBMASTERPICKING", "SPCBINNERPICKING", "PCBPROMO", "PCBIMPLANT"]
# Colonnes numériques pour l'onglet Promo (sans PCBIMPLANT)
COLONNES_NUMERIQUES_PROMO = ["PCBMASTERPICKING", "SPCBINNERPICKING", "PCBPROMO"]

def detecter_colonnes_dupliquees_brutes(contenu_fichier, nom_feuille):
    """
    Détecte les colonnes strictement dupliquées en analysant les en-têtes bruts
    sans passer par pandas qui peut automatiquement renommer les doublons
    """
    try:
        # Lecture brute des noms de colonnes (seulement la 1ʳᵉ ligne)
        raw_header = pd.read_excel(io.BytesIO(contenu_fichier), engine="pyxlsb", 
                                 sheet_name=nom_feuille, header=None, nrows=1).iloc[0].tolist()
        
        deja_vus = {}
        duplicatas = []
        details_duplicatas = []

        for i, nom in enumerate(raw_header):
            # Convertir en string pour éviter les problèmes avec les valeurs NaN
            nom_str = str(nom) if pd.notna(nom) else f"Colonne_vide_{i}"
            
            if nom_str in deja_vus:
                duplicatas.append((nom_str, deja_vus[nom_str], i))
                details_duplicatas.append(f"'{nom_str}' en colonnes Excel {deja_vus[nom_str]+1} et {i+1}")
            else:
                deja_vus[nom_str] = i

        if duplicatas:
            return {
                'statut': 'ERREUR',
                'nb_duplicatas': len(duplicatas),
                'duplicatas': duplicatas,
                'details': f"{len(duplicatas)} colonne(s) dupliquée(s) : " + " | ".join(details_duplicatas),
                'details_liste': details_duplicatas
            }
        else:
            return {
                'statut': 'OK',
                'nb_duplicatas': 0,
                'duplicatas': [],
                'details': 'Aucune colonne strictement dupliquée détectée',
                'details_liste': []
            }
            
    except Exception as e:
        return {
            'statut': 'ERREUR',
            'nb_duplicatas': 0,
            'duplicatas': [],
            'details': f"Erreur lors de la détection des doublons : {str(e)}",
            'details_liste': []
        }

def verifier_colonnes_dupliquees(df, nom_feuille):
    """Vérifie s'il y a des colonnes dupliquées dans les en-têtes (ligne 1) - Ancienne méthode"""
    colonnes = df.columns.tolist()
    colonnes_dupliquees = []
    colonnes_vues = {}
    
    for i, col in enumerate(colonnes):
        if col in colonnes_vues:
            if col not in colonnes_dupliquees:
                colonnes_dupliquees.append(col)
        else:
            colonnes_vues[col] = i
    
    if colonnes_dupliquees:
        return {
            'statut': 'ERREUR',
            'colonnes_dupliquees': colonnes_dupliquees,
            'details': f"Colonnes dupliquées détectées: {', '.join(colonnes_dupliquees)}"
        }
    else:
        return {
            'statut': 'OK',
            'colonnes_dupliquees': [],
            'details': 'Aucune colonne dupliquée détectée'
        }

def verifier_colonnes_obligatoires(df, colonnes_requises, nom_feuille):
    """Vérifie la présence des colonnes obligatoires dans une feuille"""
    colonnes_presentes = df.columns.tolist()
    colonnes_manquantes = [col for col in colonnes_requises if col not in colonnes_presentes]

    return {
        'nom_feuille': nom_feuille,
        'colonnes_manquantes': colonnes_manquantes,
        'nb_colonnes_manquantes': len(colonnes_manquantes),
        'nb_colonnes_totales': len(colonnes_requises),
        'statut': 'OK' if len(colonnes_manquantes) == 0 else 'ERREUR'
    }

def verifier_codeclient(df):
    """Vérifie la validité de la colonne CODECLIENT"""
    if "CODECLIENT" not in df.columns:
        return {'statut': 'ABSENT', 'details': 'Colonne CODECLIENT absente'}

    # Définir les lignes Excel à exclure et convertir en index pandas (Excel line - 2)
    lignes_exclues_excel = [2, 3, 4, 5, 6]
    index_exclus = [i - 2 for i in lignes_exclues_excel]

    # Exclure les lignes concernées
    df_codeclient = df.drop(index=index_exclus, errors='ignore')

    # Trouver la dernière ligne où CODECLIENT est rempli (zone de données utiles)
    codeclient_rempli = ~(df_codeclient["CODECLIENT"].isna() | (df_codeclient["CODECLIENT"].astype(str).str.strip() == ""))

    if codeclient_rempli.sum() == 0:
        return {'statut': 'ERREUR', 'details': 'Aucune donnée trouvée dans CODECLIENT'}

    # Déterminer la zone de données utiles (jusqu'à la dernière ligne avec CODECLIENT rempli)
    derniere_ligne_utile = codeclient_rempli[codeclient_rempli].index.max()
    zone_utile = df_codeclient.loc[:derniere_ligne_utile]

    # Vérifier dans la zone utile
    codeclient_vide_zone = zone_utile["CODECLIENT"].isna() | (zone_utile["CODECLIENT"].astype(str).str.strip() == "")
    codeclient_invalides_zone = ~zone_utile["CODECLIENT"].isin(["FRCA", "FRCH"]) & ~codeclient_vide_zone

    nb_vides = codeclient_vide_zone.sum()
    nb_invalides = codeclient_invalides_zone.sum()
    nb_lignes_utiles = len(zone_utile)

    details = []
    lignes_vides = []
    lignes_invalides = []
    valeurs_invalides = []

    if nb_vides > 0:
        lignes_vides = (codeclient_vide_zone[codeclient_vide_zone].index + 2).tolist()
        details.append(f'{nb_vides} lignes vides (lignes Excel: {lignes_vides})')

    if nb_invalides > 0:
        lignes_invalides = (codeclient_invalides_zone[codeclient_invalides_zone].index + 2).tolist()
        # Récupérer les valeurs invalides
        valeurs_invalides = zone_utile.loc[codeclient_invalides_zone, "CODECLIENT"].unique().tolist()
        valeurs_invalides = [str(v) for v in valeurs_invalides if pd.notna(v)]
        details.append(f'{nb_invalides} codes invalides: {valeurs_invalides} (lignes Excel: {lignes_invalides})')

    # Ajouter info sur la zone analysée
    details_zone = f"Zone analysée: {nb_lignes_utiles} lignes (jusqu'à ligne Excel {derniere_ligne_utile + 2})"

    if nb_vides == 0 and nb_invalides == 0:
        return {'statut': 'OK', 'details': f'Tous les codes clients sont valides (hors lignes exclues). {details_zone}'}
    else:
        return {
            'statut': 'ERREUR',
            'details': ' | '.join(details) + f' | {details_zone}',
            'lignes_vides': lignes_vides,
            'lignes_invalides': lignes_invalides,
            'valeurs_invalides': valeurs_invalides,
            'zone_analysee': nb_lignes_utiles
        }

def verifier_client(df):
    """Vérifie la validité de la colonne CLIENT pour l'onglet PROMO"""
    if "CLIENT" not in df.columns:
        return {'statut': 'ABSENT', 'details': 'Colonne CLIENT absente'}

    # Définir les lignes Excel à exclure et convertir en index pandas (Excel line - 2)
    lignes_exclues_excel = [2, 3, 4, 5, 6]
    index_exclus = [i - 2 for i in lignes_exclues_excel]

    # Exclure les lignes concernées
    df_client = df.drop(index=index_exclus, errors='ignore')

    # Trouver la dernière ligne où CLIENT est rempli (zone de données utiles)
    client_rempli = ~(df_client["CLIENT"].isna() | (df_client["CLIENT"].astype(str).str.strip() == ""))

    if client_rempli.sum() == 0:
        return {'statut': 'ERREUR', 'details': 'Aucune donnée trouvée dans CLIENT'}

    # Déterminer la zone de données utiles (jusqu'à la dernière ligne avec CLIENT rempli)
    derniere_ligne_utile = client_rempli[client_rempli].index.max()
    zone_utile = df_client.loc[:derniere_ligne_utile]

    # Vérifier dans la zone utile
    client_vide_zone = zone_utile["CLIENT"].isna() | (zone_utile["CLIENT"].astype(str).str.strip() == "")
    client_invalides_zone = ~zone_utile["CLIENT"].isin(["FRCA", "FRCH"]) & ~client_vide_zone

    nb_vides = client_vide_zone.sum()
    nb_invalides = client_invalides_zone.sum()
    nb_lignes_utiles = len(zone_utile)

    details = []
    lignes_vides = []
    lignes_invalides = []
    valeurs_invalides = []

    if nb_vides > 0:
        lignes_vides = (client_vide_zone[client_vide_zone].index + 2).tolist()
        details.append(f'{nb_vides} lignes vides (lignes Excel: {lignes_vides})')

    if nb_invalides > 0:
        lignes_invalides = (client_invalides_zone[client_invalides_zone].index + 2).tolist()
        # Récupérer les valeurs invalides
        valeurs_invalides = zone_utile.loc[client_invalides_zone, "CLIENT"].unique().tolist()
        valeurs_invalides = [str(v) for v in valeurs_invalides if pd.notna(v)]
        details.append(f'{nb_invalides} codes invalides: {valeurs_invalides} (lignes Excel: {lignes_invalides})')

    # Ajouter info sur la zone analysée
    details_zone = f"Zone analysée: {nb_lignes_utiles} lignes (jusqu'à ligne Excel {derniere_ligne_utile + 2})"

    if nb_vides == 0 and nb_invalides == 0:
        return {'statut': 'OK', 'details': f'Tous les codes clients sont valides (hors lignes exclues). {details_zone}'}
    else:
        return {
            'statut': 'ERREUR',
            'details': ' | '.join(details) + f' | {details_zone}',
            'lignes_vides': lignes_vides,
            'lignes_invalides': lignes_invalides,
            'valeurs_invalides': valeurs_invalides,
            'zone_analysee': nb_lignes_utiles
        }

def verifier_colonnes_numeriques(df, colonnes_num, colonne_reference="CODECLIENT"):
    """Vérifie que les colonnes spécifiées contiennent uniquement des chiffres"""
    resultats = {}

    # Définir les lignes Excel à exclure et convertir en index pandas (Excel line - 2)
    lignes_exclues_excel = [2, 3, 4, 5, 6]
    index_exclus = [i - 2 for i in lignes_exclues_excel]

    # Exclure les lignes concernées
    df_col = df.drop(index=index_exclus, errors='ignore')

    # Déterminer la zone de données utiles basée sur la colonne de référence
    if colonne_reference in df_col.columns:
        ref_rempli = ~(df_col[colonne_reference].isna() | (df_col[colonne_reference].astype(str).str.strip() == ""))
        if ref_rempli.sum() > 0:
            derniere_ligne_utile = ref_rempli[ref_rempli].index.max()
            df_col = df_col.loc[:derniere_ligne_utile]

    for col in colonnes_num:
        if col not in df.columns:
            resultats[col] = {'statut': 'ABSENT', 'nb_erreurs': 0, 'lignes_erreur': [], 'valeurs_non_numeriques': []}
        else:
            # Vérifier les valeurs numériques avec gestion des NaN
            non_numeriques = ~df_col[col].astype(str).str.strip().str.fullmatch(r'\d+', na=True)
            nb_erreurs = non_numeriques.sum()
            lignes_erreur = (non_numeriques[non_numeriques].index + 2).tolist() if nb_erreurs > 0 else []

            # Récupérer les valeurs non numériques uniques
            valeurs_non_numeriques = []
            if nb_erreurs > 0:
                valeurs_non_num = df_col.loc[non_numeriques, col].astype(str).str.strip().unique()
                valeurs_non_numeriques = [v for v in valeurs_non_num if v != 'nan' and v != '']

            resultats[col] = {
                'statut': 'OK' if nb_erreurs == 0 else 'ERREUR',
                'nb_erreurs': nb_erreurs,
                'lignes_erreur': lignes_erreur,
                'valeurs_non_numeriques': valeurs_non_numeriques[:10],  # Limiter à 10 valeurs pour éviter l'encombrement
                'zone_analysee': len(df_col)
            }

    return resultats

def traiter_fichier(nom_fichier, contenu):
    """Traite un fichier XLSB et retourne les résultats de vérification"""
    resultats = {
        'nom_fichier': nom_fichier,
        'statut_global': 'OK',
        'erreurs': []
    }

    try:
        # Vérification de l'onglet "Référentiel"
        try:
            df_ref = pd.read_excel(io.BytesIO(contenu), engine="pyxlsb", sheet_name="Référentiel")
            resultats['referentiel'] = {
                'colonnes_dupliquees_brutes': detecter_colonnes_dupliquees_brutes(contenu, "Référentiel"),
                'colonnes': verifier_colonnes_obligatoires(df_ref, COLONNES_REFERENTIEL, "Référentiel"),
                'codeclient': verifier_codeclient(df_ref),
                'colonnes_numeriques': verifier_colonnes_numeriques(df_ref, COLONNES_NUMERIQUES, "CODECLIENT"),
                'nb_lignes': len(df_ref)
            }
        except Exception as e:
            resultats['referentiel'] = {'erreur': f"Impossible de lire l'onglet Référentiel: {str(e)}"}
            resultats['statut_global'] = 'ERREUR'

        # Vérification de l'onglet "Promo"
        try:
            df_promo = pd.read_excel(io.BytesIO(contenu), engine="pyxlsb", sheet_name="Promo")
            resultats['promo'] = {
                'colonnes_dupliquees_brutes': detecter_colonnes_dupliquees_brutes(contenu, "Promo"),
                'colonnes': verifier_colonnes_obligatoires(df_promo, COLONNES_PROMO, "Promo"),
                'client': verifier_client(df_promo),
                'colonnes_numeriques': verifier_colonnes_numeriques(df_promo, COLONNES_NUMERIQUES_PROMO, "CLIENT"),
                'nb_lignes': len(df_promo)
            }
        except Exception as e:
            resultats['promo'] = {'erreur': f"Impossible de lire l'onglet Promo: {str(e)}"}
            resultats['statut_global'] = 'ERREUR'

        # Déterminer le statut global
        if 'referentiel' in resultats and 'colonnes' in resultats['referentiel']:
            if resultats['referentiel']['colonnes_dupliquees_brutes']['statut'] == 'ERREUR':
                resultats['statut_global'] = 'ERREUR'
            if resultats['referentiel']['colonnes']['statut'] == 'ERREUR':
                resultats['statut_global'] = 'ERREUR'
            if resultats['referentiel']['codeclient']['statut'] == 'ERREUR':
                resultats['statut_global'] = 'ERREUR'
            for col_num in resultats['referentiel']['colonnes_numeriques'].values():
                if col_num['statut'] == 'ERREUR':
                    resultats['statut_global'] = 'ERREUR'

        if 'promo' in resultats and 'colonnes' in resultats['promo']:
            if resultats['promo']['colonnes_dupliquees_brutes']['statut'] == 'ERREUR':
                resultats['statut_global'] = 'ERREUR'
            if resultats['promo']['colonnes']['statut'] == 'ERREUR':
                resultats['statut_global'] = 'ERREUR'
            if resultats['promo']['client']['statut'] == 'ERREUR':
                resultats['statut_global'] = 'ERREUR'
            # Vérifier aussi les colonnes numériques de Promo
            if 'colonnes_numeriques' in resultats['promo']:
                for col_num in resultats['promo']['colonnes_numeriques'].values():
                    if col_num['statut'] == 'ERREUR':
                        resultats['statut_global'] = 'ERREUR'

    except Exception as e:
        resultats['erreur_generale'] = str(e)
        resultats['statut_global'] = 'ERREUR'

    return resultats

def afficher_resultats_streamlit(tous_resultats):
    """Affiche les résultats dans Streamlit"""
    # Résumé global
    total_fichiers = len(tous_resultats)
    fichiers_ok = sum(1 for r in tous_resultats if r['statut_global'] == 'OK')
    fichiers_erreur = total_fichiers - fichiers_ok

    # Métriques principales
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total fichiers", total_fichiers)
    with col2:
        st.metric("✅ Conformes", fichiers_ok, delta=None)
    with col3:
        st.metric("❌ Avec erreurs", fichiers_erreur, delta=None)

    # Détail par fichier
    for i, resultat in enumerate(tous_resultats, 1):
        with st.expander(f"📄 {resultat['nom_fichier']} - {'✅ CONFORME' if resultat['statut_global'] == 'OK' else '❌ NON CONFORME'}", 
                        expanded=resultat['statut_global'] == 'ERREUR'):
            
            # Référentiel
            if 'referentiel' in resultat:
                st.subheader("📑 Onglet Référentiel")
                
                if 'erreur' in resultat['referentiel']:
                    st.error(f"🔴 {resultat['referentiel']['erreur']}")
                else:
                    ref = resultat['referentiel']
                    st.info(f"Nombre de lignes: {ref['nb_lignes']}")

                    # Vérification des colonnes dupliquées (nouvelle méthode améliorée)
                    dup_status = ref['colonnes_dupliquees_brutes']
                    if dup_status['statut'] == 'OK':
                        st.success(f"✅ Colonnes dupliquées: {dup_status['details']}")
                    else:
                        st.error(f"❌ Colonnes dupliquées: {dup_status['details']}")
                        if dup_status['details_liste']:
                            with st.expander("Détail des colonnes dupliquées"):
                                for detail in dup_status['details_liste']:
                                    st.write(f"• {detail}")

                    # Colonnes
                    col_status = ref['colonnes']
                    if col_status['statut'] == 'OK':
                        st.success(f"✅ Colonnes: Toutes présentes ({col_status['nb_colonnes_totales']})")
                    else:
                        st.error(f"❌ Colonnes: {col_status['nb_colonnes_manquantes']} manquantes sur {col_status['nb_colonnes_totales']}")
                        with st.expander("Voir les colonnes manquantes"):
                            for col in col_status['colonnes_manquantes']:
                                st.write(f"• {col}")

                    # CODECLIENT
                    cc_status = ref['codeclient']
                    if cc_status['statut'] == 'OK':
                        st.success(f"✅ CODECLIENT: {cc_status['details']}")
                    else:
                        st.error(f"❌ CODECLIENT: {cc_status['details']}")

                    # Colonnes numériques
                    st.write("**Vérification des colonnes numériques:**")
                    for col_name, col_info in ref['colonnes_numeriques'].items():
                        if col_info['statut'] == 'ABSENT':
                            st.warning(f"⚠️ {col_name}: Colonne absente")
                        elif col_info['statut'] == 'OK':
                            st.success(f"✅ {col_name}: Valeurs numériques")
                        else:
                            st.error(f"❌ {col_name}: {col_info['nb_erreurs']} valeurs non numériques")
                            if col_info['valeurs_non_numeriques']:
                                st.write(f"Exemples de valeurs: {col_info['valeurs_non_numeriques']}")

            # Promo
            if 'promo' in resultat:
                st.subheader("📑 Onglet Promo")
                
                if 'erreur' in resultat['promo']:
                    st.error(f"🔴 {resultat['promo']['erreur']}")
                else:
                    promo = resultat['promo']
                    st.info(f"Nombre de lignes: {promo['nb_lignes']}")

                    # Vérification des colonnes dupliquées (nouvelle méthode améliorée)
                    dup_status = promo['colonnes_dupliquees_brutes']
                    if dup_status['statut'] == 'OK':
                        st.success(f"✅ Colonnes dupliquées: {dup_status['details']}")
                    else:
                        st.error(f"❌ Colonnes dupliquées: {dup_status['details']}")
                        if dup_status['details_liste']:
                            with st.expander("Détail des colonnes dupliquées"):
                                for detail in dup_status['details_liste']:
                                    st.write(f"• {detail}")

                    # Colonnes
                    col_status = promo['colonnes']
                    if col_status['statut'] == 'OK':
                        st.success(f"✅ Colonnes: Toutes présentes ({col_status['nb_colonnes_totales']})")
                    else:
                        st.error(f"❌ Colonnes: {col_status['nb_colonnes_manquantes']} manquantes sur {col_status['nb_colonnes_totales']}")
                        with st.expander("Voir les colonnes manquantes"):
                            for col in col_status['colonnes_manquantes']:
                                st.write(f"• {col}")

                    # CLIENT
                    client_status = promo['client']
                    if client_status['statut'] == 'OK':
                        st.success(f"✅ CLIENT: {client_status['details']}")
                    else:
                        st.error(f"❌ CLIENT: {client_status['details']}")

                    # Colonnes numériques pour Promo (sans PCBIMPLANT)
                    if 'colonnes_numeriques' in promo:
                        st.write("**Vérification des colonnes numériques:**")
                        for col_name, col_info in promo['colonnes_numeriques'].items():
                            if col_info['statut'] == 'ABSENT':
                                st.warning(f"⚠️ {col_name}: Colonne absente")
                            elif col_info['statut'] == 'OK':
                                st.success(f"✅ {col_name}: Valeurs numériques")
                            else:
                                st.error(f"❌ {col_name}: {col_info['nb_erreurs']} valeurs non numériques")
                                if col_info['valeurs_non_numeriques']:
                                    st.write(f"Exemples de valeurs: {col_info['valeurs_non_numeriques']}")

            # Erreur générale
            if 'erreur_generale' in resultat:
                st.error(f"🔴 Erreur générale: {resultat['erreur_generale']}")

# Interface Streamlit
def main():
    st.title("📊 Vérificateur de fichiers Excel (.xlsb)")
    st.markdown("---")
    
    # Description
    st.markdown("""
    ### 📋 Description
    Cet outil vérifie la conformité de vos fichiers Excel (.xlsb) en analysant :
    - **Vérification des colonnes dupliquées** : Détecte les colonnes en double dans les en-têtes
    - **Onglet Référentiel** : Présence des colonnes obligatoires, validité des codes clients, format des colonnes numériques
    - **Onglet Promo** : Présence des colonnes obligatoires, validité des codes clients, format des colonnes numériques
    """)
    

    # Upload des fichiers
    st.header("📂 Upload des fichiers")
    uploaded_files = st.file_uploader(
        "Sélectionnez vos fichiers .xlsb",
        type=['xlsb'],
        accept_multiple_files=True,
        help="Vous pouvez sélectionner plusieurs fichiers à la fois"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} fichier(s) sélectionné(s)")
        
        # Bouton de traitement
        if st.button("🚀 Lancer la vérification", type="primary"):
            tous_resultats = []
            
            # Barre de progression
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f'Traitement en cours: {uploaded_file.name}...')
                progress_bar.progress((i + 1) / len(uploaded_files))
                
                try:
                    # Lire le contenu du fichier
                    contenu = uploaded_file.read()
                    uploaded_file.seek(0)  # Reset pour une éventuelle relecture
                    
                    # Traiter le fichier
                    resultat = traiter_fichier(uploaded_file.name, contenu)
                    tous_resultats.append(resultat)
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors du traitement de {uploaded_file.name}: {str(e)}")
                    st.write("Détails de l'erreur:")
                    st.code(traceback.format_exc())
            
            status_text.text('Traitement terminé!')
            
            # Affichage des résultats
            if tous_resultats:
                st.header("📈 Résultats de la vérification")
                afficher_resultats_streamlit(tous_resultats)
                
                # Option de téléchargement (optionnel)
                st.markdown("---")
                st.subheader("💾 Export des résultats")
                
                # Créer un résumé textuel
                rapport_texte = f"RAPPORT DE VÉRIFICATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                rapport_texte += "=" * 80 + "\n\n"
                
                total_fichiers = len(tous_resultats)
                fichiers_ok = sum(1 for r in tous_resultats if r['statut_global'] == 'OK')
                fichiers_erreur = total_fichiers - fichiers_ok
                
                rapport_texte += f"RÉSUMÉ GLOBAL\n"
                rapport_texte += f"Total fichiers traités: {total_fichiers}\n"
                rapport_texte += f"Fichiers conformes: {fichiers_ok}\n"
                rapport_texte += f"Fichiers avec erreurs: {fichiers_erreur}\n\n"
                
                for resultat in tous_resultats:
                    rapport_texte += f"FICHIER: {resultat['nom_fichier']}\n"
                    rapport_texte += f"Statut: {'CONFORME' if resultat['statut_global'] == 'OK' else 'NON CONFORME'}\n"
                    rapport_texte += "-" * 60 + "\n\n"
                
                # Bouton de téléchargement du rapport
                st.download_button(
                    label="📄 Télécharger le rapport complet",
                    data=rapport_texte,
                    file_name=f"rapport_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
    
    else:
        st.info("👆 Veuillez sélectionner des fichiers .xlsb pour commencer la vérification")
        
        # Exemple d'utilisation
        with st.expander("📖 Guide d'utilisation"):
            st.markdown("""
            ### Comment utiliser cet outil :
            
            1. **Sélectionnez vos fichiers** : Cliquez sur "Browse files" et sélectionnez un ou plusieurs fichiers .xlsb
            2. **Lancez la vérification** : Cliquez sur le bouton "🚀 Lancer la vérification"
            3. **Consultez les résultats** : Les résultats s'affichent avec des détails pour chaque fichier
            4. **Téléchargez le rapport** : Optionnel, vous pouvez télécharger un rapport complet
            
            ### Structure attendue des fichiers :
            
            **Onglet "Référentiel"** doit contenir :
            - Toutes les colonnes obligatoires (voir sidebar)
            - Colonne CODECLIENT avec des valeurs "FRCA" ou "FRCH" uniquement
            - Colonnes numériques avec des valeurs numériques uniquement
            
            **Onglet "Promo"** doit contenir :
            - Toutes les colonnes obligatoires spécifiques à Promo
            - Colonne CLIENT avec des valeurs "FRCA" ou "FRCH" uniquement
            - Colonnes numériques avec des valeurs numériques uniquement
            
            ### Notes importantes :
            - Les lignes Excel 2 à 6 sont automatiquement exclues de l'analyse
            - Seules les données jusqu'à la dernière ligne contenant des codes clients sont analysées
            - Les colonnes numériques vérifiées : PCBMASTERPICKING, SPCBINNERPICKING, PCBPROMO, PCBIMPLANT
            """)

if __name__ == "__main__":
    main()

