import streamlit as st
import google.generativeai as genai
import json
import os
from PIL import Image

DATA_FILE = "recipes.json"

def load_recipes():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_all_recipes(recipes):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(recipes, f, ensure_ascii=False, indent=4)

def save_recipe_to_db(recipe):
    recipes = load_recipes()
    recipes.append(recipe)
    save_all_recipes(recipes)

st.set_page_config(
    page_title="High-Protein Rezepte",
    page_icon="🥗",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .stButton>button {
        width: 100% !important;
        border-radius: 12px;
        height: 3em;
        font-weight: bold;
    }
    .macro-badge {
        background-color: #f0f2f6;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.9em;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🥗 Unser Rezept-Hub")
st.caption("High-Protein & Kalorienbewusst für 2 Personen")

tab1, tab2, tab3, tab4 = st.tabs(["📸 Yazio", "🎥 Instagram", "📖 Sammlung", "🤖 KI-Assistent"])

# --- TAB 1: YAZIO IMPORT ---
with tab1:
    st.subheader("Neues Rezept aus Yazio-Screenshot")
    api_key = st.text_input("Gemini API-Key:", type="password", key="key_t1")
    uploaded_file = st.file_uploader("Yazio-Screenshot (Mahlzeit oder Rezept mit Anleitung) hochladen...", type=["jpg", "jpeg", "png"], key="img_t1")
    
    if uploaded_file and api_key:
        image = Image.open(uploaded_file)
        st.image(image, caption="Screenshot (Basis = 1 Portion)", use_column_width=True)
        custom_title = st.text_input("Name des Rezepts (optional):", placeholder="z.B. Saftige Hähnchen-Bowl", key="title_t1")
        
        if st.button("🚀 Nährwerte, Zutaten & Anleitung auslesen", key="btn_t1"):
            with st.spinner("Analysiere Yazio-Daten..."):
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Erweiterter Prompt für Titel, Nährwerte pro Portion & Anleitung
                prompt = """
                Analysiere diesen Yazio Screenshot (Mahlzeit oder Rezept).
                Extrahiere die Daten streng im folgenden JSON Format:
                {
                    "titel": "Name des Rezepts falls im Bild erkennbar, sonst leer lassen",
                    "kalorien": 0,
                    "protein": 0,
                    "kohlenhydrate": 0,
                    "fett": 0,
                    "zutaten": ["Zutat 1 mit Menge", "Zutat 2 mit Menge"],
                    "anleitung": "Falls der Punkt Anleitung oder Zubereitungsschritte vorhanden ist, schreibe die Schritte hier rein, sonst leer lassen"
                }
                WICHTIG: Kalorien, Protein, Kohlenhydrate und Fett müssen sich immer streng auf 1 PORTION beziehen!
                Gib NUR das reine JSON ohne Markdown zurück!
                """
                try:
                    response = model.generate_content([prompt, image])
                    recipe_data = json.loads(response.text.replace("```json", "").replace("```", "").strip())
                    
                    # Titel-Priorität: Eingabe > erkannt im Bild > Fallback
                    if custom_title:
                        recipe_data["titel"] = custom_title
                    elif not recipe_data.get("titel"):
                        recipe_data["titel"] = "Mein High-Protein Rezept"
                        
                    recipe_data["quelle"] = "Yazio"
                    st.session_state['extracted_recipe'] = recipe_data
                    st.success("Daten & Anleitung erfolgreich extrahiert!")
                except Exception as e:
                    st.error(f"Fehler bei der Erkennung: {e}")

    if 'extracted_recipe' in st.session_state and st.session_state.get('extracted_recipe', {}).get('quelle') == "Yazio":
        rec = st.session_state['extracted_recipe']
        st.markdown("---")
        st.markdown(f"### Voransicht: {rec['titel']}")
        
        col_cat1, col_cat2 = st.columns(2)
        with col_cat1:
            mahlzeit = st.selectbox("Mahlzeit-Typ:", ["Hauptmahlzeit", "Frühstück"], key="cat_mahlzeit")
        with col_cat2:
            geschmack = st.selectbox("Geschmack:", ["Herzhaft", "Süß"], key="cat_geschmack")

        portions = st.slider("Für wie viele Personen kocht ihr meistens?", min_value=1, max_value=6, value=2, key="p_t1")
        
        # Automatisch erkannte Anleitung als Standard im Notizfeld eintragen
        default_notes = rec.get("anleitung", "")
        notes = st.text_area("Zubereitungshinweise & Notizen (aus Yazio übernommen):", value=default_notes, placeholder="z.B. Herdstufe 7...", key="notes_t1")

        st.markdown("**Nährwerte pro Portion (Basis aus Screenshot):**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Kcal", int(rec['kalorien']))
        c2.metric("Protein", f"{round(float(rec['protein']), 1)}g")
        c3.metric("Carbs", f"{round(float(rec['kohlenhydrate']), 1)}g")
        c4.metric("Fett", f"{round(float(rec['fett']), 1)}g")
        
        st.write("**Zutaten (1 Portion):**")
        for z in rec['zutaten']:
            st.write(f"- {z}")
            
        if st.button("💾 In Sammlung speichern", key="save_t1"):
            rec['portions_base'] = portions
            rec['notes'] = notes
            rec['mahlzeit'] = mahlzeit
            rec['geschmack'] = geschmack
            save_recipe_to_db(rec)
            st.success(f"Rezept '{rec['titel']}' erfolgreich gespeichert! 🎉")
            del st.session_state['extracted_recipe']

# --- TAB 2: INSTAGRAM IMPORT ---
with tab2:
    st.subheader("🎥 Rezept aus Instagram Reel")
    api_key_ig = st.text_input("Gemini API-Key:", type="password", key="key_t2")
    reel_link = st.text_input("Instagram Reel Link:", placeholder="https://www.instagram.com/reel/...", key="link_t2")
    reel_caption = st.text_area("Oder Beschreibungstext kopieren:", placeholder="Zutaten: ... Zubereitung: ...", key="cap_t2")
    reel_image = st.file_uploader("Optional: Screenshot aus Reel...", type=["jpg", "jpeg", "png"], key="img_t2")
    custom_title_ig = st.text_input("Name des Rezepts (optional):", placeholder="z.B. Protein Pizza Wrap", key="title_t2")

    if st.button("🚀 Rezept aus Reel generieren", key="btn_t2"):
        if not api_key_ig:
            st.error("Bitte gib deinen API-Key ein.")
        else:
            with st.spinner("Analysiere Reel..."):
                genai.configure(api_key=api_key_ig)
                model = genai.GenerativeModel('gemini-1.5-flash')
                ig_prompt = f"""
                Analysiere dieses Instagram Koch-Reel (Link: {reel_link}, Text: {reel_caption}). 
                Extrahiere das Rezept gerechnet auf 1 PORTION im JSON-Format:
                {{
                    "titel": "Name des Gerichts",
                    "kalorien": 450,
                    "protein": 35,
                    "kohlenhydrate": 40,
                    "fett": 12,
                    "zutaten": ["Zutat 1", "Zutat 2"],
                    "notes": "Schritt-für-Schritt Zubereitungsanleitung aus dem Reel"
                }}
                Gib NUR reines JSON ohne Markdown zurück!
                """
                contents = [ig_prompt]
                if reel_image:
                    contents.append(Image.open(reel_image))
                try:
                    response = model.generate_content(contents)
                    recipe_data = json.loads(response.text.replace("```json", "").replace("```", "").strip())
                    if custom_title_ig:
                        recipe_data["titel"] = custom_title_ig
                    recipe_data["quelle"] = "Instagram"
                    st.session_state['extracted_reel'] = recipe_data
                    st.success("Erfolgreich aus Reel extrahiert!")
                except Exception as e:
                    st.error(f"Fehler: {e}")

    if 'extracted_reel' in st.session_state:
        rec_ig = st.session_state['extracted_reel']
        st.markdown("---")
        st.markdown(f"### Voransicht: {rec_ig['titel']}")
        
        col_cat1, col_cat2 = st.columns(2)
        with col_cat1:
            mahlzeit_ig = st.selectbox("Mahlzeit-Typ:", ["Hauptmahlzeit", "Frühstück"], key="cat_m_ig")
        with col_cat2:
            geschmack_ig = st.selectbox("Geschmack:", ["Herzhaft", "Süß"], key="cat_g_ig")

        portions_ig = st.slider("Standard-Portionen:", min_value=1, max_value=6, value=2, key="p_t2")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Kcal (1 Port.)", int(rec_ig['kalorien']))
        c2.metric("Protein", f"{rec_ig['protein']}g")
        c3.metric("Carbs", f"{rec_ig['kohlenhydrate']}g")
        c4.metric("Fett", f"{rec_ig['fett']}g")
        
        st.write("**Zutaten:**")
        for z in rec_ig['zutaten']:
            st.write(f"- {z}")
        st.write("**Zubereitung:**")
        st.info(rec_ig.get('notes', 'Keine Anleitung.'))
        
        if st.button("💾 In Sammlung speichern", key="save_t2"):
            rec_ig['portions_base'] = portions_ig
            rec_ig['mahlzeit'] = mahlzeit_ig
            rec_ig['geschmack'] = geschmack_ig
            save_recipe_to_db(rec_ig)
            st.success(f"Rezept '{rec_ig['titel']}' gespeichert! 🎉")
            del st.session_state['extracted_reel']

# --- TAB 3: SAMMLUNG, SPALTENANZEIGE & BEARBEITEN ---
with tab3:
    st.subheader("📖 Eure Rezept-Sammlung")
    all_recipes = load_recipes()
    
    if not all_recipes:
        st.info("Bisher noch keine Rezepte gespeichert.")
    else:
        st.markdown("##### 🔍 Filter & Suche")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            filter_mahlzeit = st.selectbox("Nach Mahlzeit filtern:", ["Alle", "Hauptmahlzeit", "Frühstück"])
        with f_col2:
            filter_geschmack = st.selectbox("Nach Geschmack filtern:", ["Alle", "Herzhaft", "Süß"])
            
        ingredient_search = st.text_input("Nach Name oder Zutat suchen...", "")
        st.markdown("---")
        
        # Filteranwendung
        filtered_indices = []
        for orig_idx, r in enumerate(all_recipes):
            if filter_mahlzeit != "Alle" and r.get('mahlzeit', 'Hauptmahlzeit') != filter_mahlzeit:
                continue
            if filter_geschmack != "Alle" and r.get('geschmack', 'Herzhaft') != filter_geschmack:
                continue
            query = ingredient_search.lower()
            if query:
                match_title = query in r['titel'].lower()
                match_ingredient = any(query in z.lower() for z in r['zutaten'])
                if not (match_title or match_ingredient):
                    continue
            filtered_indices.append(orig_idx)

        if not filtered_indices:
            st.warning("Keine Rezepte gefunden.")
        else:
            for orig_idx in reversed(filtered_indices):
                r = all_recipes[orig_idx]
                
                # NEU: Überschriften-Design mit 2 SPALTEN für Kalorien & Protein pro Portion
                title_label = f"🍽️ {r['titel']}  |  🔥 {r['kalorien']} kcal  |  🥩 {r['protein']}g Protein (pro Port.)"
                
                with st.expander(title_label):
                    # Bearbeitungs-Modus Umschaltung
                    edit_mode_key = f"edit_mode_{orig_idx}"
                    if edit_mode_key not in st.session_state:
                        st.session_state[edit_mode_key] = False
                        
                    if not st.session_state[edit_mode_key]:
                        # --- NORMALE ANSICHT ---
                        view_portions = st.slider("Portionen umrechnen:", min_value=1, max_value=6, value=r.get('portions_base', 2), key=f"slider_{orig_idx}")
                        
                        cols = st.columns(4)
                        cols[0].metric("Kcal Gesamt", int(r['kalorien']) * view_portions)
                        cols[1].metric("Protein Gesamt", f"{round(float(r['protein']) * view_portions, 1)}g")
                        cols[2].metric("Carbs Gesamt", f"{round(float(r['kohlenhydrate']) * view_portions, 1)}g")
                        cols[3].metric("Fett Gesamt", f"{round(float(r['fett']) * view_portions, 1)}g")
                        
                        st.write("**Zutaten (1 Portion):**")
                        for z in r['zutaten']:
                            st.write(f"• {z}")
                            
                        if r.get('notes'):
                            st.markdown("---")
                            st.write(f"📝 **Zubereitung & Notizen:**\n> {r['notes']}")
                            
                        st.markdown("---")
                        c_btn1, c_btn2 = st.columns(2)
                        with c_btn1:
                            if st.button("✏️ Rezept bearbeiten", key=f"edit_btn_{orig_idx}"):
                                st.session_state[edit_mode_key] = True
                                st.rerun()
                        with c_btn2:
                            if st.button("💡 KI Protein-Booster", key=f"tip_btn_{orig_idx}"):
                                with st.spinner("Generiere Tipps..."):
                                    model = genai.GenerativeModel('gemini-1.5-flash')
                                    tip_prompt = f"Hier ist ein Rezept: {json.dumps(r, ensure_ascii=False)}. Gib mir 2 kurze Protein-Booster oder Spar-Tipps auf Deutsch."
                                    try:
                                        tip_res = model.generate_content(tip_prompt)
                                        st.info(tip_res.text)
                                    except Exception:
                                        st.error("Bitte gib im Tab 1 deinen API-Key ein.")
                    else:
                        # --- BEARBEITUNGS-MODUS ---
                        st.markdown("#### ✏️ Rezept bearbeiten")
                        new_titel = st.text_input("Name:", value=r['titel'], key=f"e_title_{orig_idx}")
                        
                        ec1, ec2 = st.columns(2)
                        new_m = ec1.selectbox("Mahlzeit:", ["Hauptmahlzeit", "Frühstück"], index=0 if r.get('mahlzeit') == "Hauptmahlzeit" else 1, key=f"e_m_{orig_idx}")
                        new_g = ec2.selectbox("Geschmack:", ["Herzhaft", "Süß"], index=0 if r.get('geschmack') == "Herzhaft" else 1, key=f"e_g_{orig_idx}")
                        
                        mc1, mc2, mc3, mc4 = st.columns(4)
                        new_kcal = mc1.number_input("Kcal/Port.", value=int(r['kalorien']), key=f"e_kc_{orig_idx}")
                        new_p = mc2.number_input("Protein/Port.", value=float(r['protein']), key=f"e_p_{orig_idx}")
                        new_c = mc3.number_input("Carbs/Port.", value=float(r['kohlenhydrate']), key=f"e_c_{orig_idx}")
                        new_f = mc4.number_input("Fett/Port.", value=float(r['fett']), key=f"e_f_{orig_idx}")
                        
                        new_zutaten_str = st.text_area("Zutaten (eine pro Zeile):", value="\n".join(r['zutaten']), key=f"e_z_{orig_idx}")
                        new_notes = st.text_area("Zubereitung & Notizen:", value=r.get('notes', ''), key=f"e_n_{orig_idx}")
                        
                        btn_save, btn_cancel = st.columns(2)
                        with btn_save:
                            if st.button("💾 Änderungen speichern", key=f"save_edit_{orig_idx}"):
                                all_recipes[orig_idx]['titel'] = new_titel
                                all_recipes[orig_idx]['mahlzeit'] = new_m
                                all_recipes[orig_idx]['geschmack'] = new_g
                                all_recipes[orig_idx]['kalorien'] = new_kcal
                                all_recipes[orig_idx]['protein'] = new_p
                                all_recipes[orig_idx]['kohlenhydrate'] = new_c
                                all_recipes[orig_idx]['fett'] = new_f
                                all_recipes[orig_idx]['zutaten'] = [z.strip() for z in new_zutaten_str.split("\n") if z.strip()]
                                all_recipes[orig_idx]['notes'] = new_notes
                                
                                save_all_recipes(all_recipes)
                                st.session_state[edit_mode_key] = False
                                st.success("Änderungen gespeichert!")
                                st.rerun()
                        with btn_cancel:
                            if st.button("❌ Abbrechen", key=f"cancel_edit_{orig_idx}"):
                                st.session_state[edit_mode_key] = False
                                st.rerun()

# --- TAB 4: KI-ASSISTENT ---
with tab4:
    st.subheader("🤖 Euer KI-Koch-Assistent")
    st.caption("Stelle Fragen zu eurer gespeicherten Rezeptsammlung")
    
    ai_key = st.text_input("Gemini API-Key:", type="password", key="key_t4")
    user_question = st.text_input("Was möchtest du wissen?", placeholder="z.B. Welches Rezept hat den italienischen Vibe?")
    
    if st.button("🤖 Assistenten fragen", key="btn_t4"):
        if not ai_key:
            st.error("Bitte gib deinen API-Key ein.")
        elif not all_recipes:
            st.warning("Ihr habt noch keine Rezepte gespeichert!")
        else:
            with st.spinner("Durchsuche eure Rezepte..."):
                genai.configure(api_key=ai_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                context_prompt = f"""
                Du bist der persönliche Koch-Assistent für ein Paar, das High-Protein kocht. 
                Hier ist ihre aktuelle Rezeptsammlung: {json.dumps(all_recipes, ensure_ascii=False)}
                Frage: "{user_question}"
                Beantworte die Frage präzise und freundlich auf Deutsch.
                """
                try:
                    answer = model.generate_content(context_prompt)
                    st.success("Antwort des Assistenten:")
                    st.markdown(answer.text)
                except Exception as e:
                    st.error(f"Fehler: {e}")
