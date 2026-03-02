import streamlit as st
import requests
import random

# --- SEADISTUS ---
st.set_page_config(page_title="Nutikas Köök | Toidukorra Planeerija", layout="wide")

# --- CSS KUJUNDUS ---
st.markdown("""
    <style>
    .recipe-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #eee;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .ingredient-tag {
        display: inline-block;
        background-color: #e1f5fe;
        color: #01579b;
        padding: 5px 10px;
        border-radius: 15px;
        margin: 3px;
        font-size: 12px;
        font-weight: bold;
    }
    .stButton>button {
        border-radius: 20px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        background-color: #ff4b4b;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ANDMETE HALDUS (Session State) ---
if 'favorites' not in st.session_state:
    st.session_state['favorites'] = []
if 'current_recipe' not in st.session_state:
    st.session_state['current_recipe'] = None

# --- FUNKTSIOONID ---
def get_recipes_by_area(area):
    """Hangib retseptid valitud piirkonna järgi"""
    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?a={area}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('meals', [])
    return []

def get_meal_details(meal_id):
    """Hangib konkreetse toidu detailid ja retsepti"""
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('meals', [None])[0]
    return None

# --- KÜLGPANEEL ---
st.sidebar.title("🍱 Toiduplaneerija")
st.sidebar.write("Vali piirkond ja pane kokku oma menüü.")

piirkond = st.sidebar.selectbox(
    "Millist maailma kööki eelistad?",
    ["Italian", "Mexican", "Japanese", "Chinese", "French", "Indian", "Greek", "American", "British"]
)

if st.sidebar.button("🎲 Soovita juhuslikku toitu"):
    res = requests.get("https://www.themealdb.com/api/json/v1/1/random.php").json()
    st.session_state['current_recipe'] = res['meals'][0]

st.sidebar.divider()
st.sidebar.subheader("⭐ Minu Lemmikud")
for fav in st.session_state['favorites']:
    st.sidebar.write(f"- {fav}")

if st.sidebar.button("🗑️ Tühjenda lemmikud"):
    st.session_state['favorites'] = []
    st.rerun()

# --- PEALEHT ---
st.title("🍽️ Mida me täna sööme?")

# Kui piirkond valitakse, kuvame valikud
meals = get_recipes_by_area(piirkond)

if meals:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader(f"{piirkond} köögi valikud")
        selected_meal_name = st.selectbox("Vali toit nimekirjast:", [m['strMeal'] for m in meals])
        
        if st.button("Näita retsepti"):
            meal_id = next(m['idMeal'] for m in meals if m['strMeal'] == selected_meal_name)
            st.session_state['current_recipe'] = get_meal_details(meal_id)

    # Kuvame valitud retsepti detailid
    if st.session_state['current_recipe']:
        recipe = st.session_state['current_recipe']
        
        with st.container():
            st.divider()
            c1, c2 = st.columns([1, 1])
            
            with c1:
                st.image(recipe['strMealThumb'], use_container_width=True)
                if st.button("❤️ Lisa lemmikutesse"):
                    if recipe['strMeal'] not in st.session_state['favorites']:
                        st.session_state['favorites'].append(recipe['strMeal'])
                        st.success("Lisatud!")
            
            with c2:
                st.header(recipe['strMeal'])
                st.write(f"**Kategooria:** {recipe['strCategory']} | **Piirkond:** {recipe['strArea']}")
                
                # Koostisosade puhastamine (API-st tulevad nad eraldi väljadena)
                st.subheader("Koostisosad ja ostunimekiri:")
                ingredients = []
                for i in range(1, 21):
                    ing = recipe.get(f'strIngredient{i}')
                    meas = recipe.get(f'strMeasure{i}')
                    if ing and ing.strip():
                        ingredients.append(f"{ing} ({meas})")
                        st.markdown(f'<span class="ingredient-tag">{ing} - {meas}</span>', unsafe_allow_html=True)
                
                st.subheader("Valmistamine:")
                st.write(recipe['strInstructions'])
                
                if recipe['strYoutube']:
                    st.video(recipe['strYoutube'])

# --- OSTUNIMEKIRI ---
st.divider()
if st.session_state['favorites']:
    st.subheader("🛒 Sinu ostunimekirja põhi")
    st.info("Siia saad koondada asjad, mida on vaja osta sinu lemmiktoitude jaoks.")
    # Siia võiks tulevikus tekkida automaatne koondamine, 
    # praegu näitame lihtsalt, et süsteem teab lemmikuid.
    st.write("Valitud toidud planeerimiseks:", ", ".join(st.session_state['favorites']))
else:
    st.caption("Lisa toite lemmikutesse, et siin näha kokkuvõtet.")
