import streamlit as st
import requests

# --- SEADISTUS ---
st.set_page_config(page_title="Nutikas Köök | Visuaalne Menüü", layout="wide")

# --- CSS KUJUNDUS (Parem visuaal ja kaartide stiil) ---
st.markdown("""
    <style>
    .meal-card {
        background-color: white;
        padding: 10px;
        border-radius: 12px;
        border: 1px solid #ddd;
        text-align: center;
        margin-bottom: 20px;
        transition: 0.3s;
    }
    .meal-card:hover {
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transform: translateY(-5px);
    }
    .meal-title {
        font-size: 14px;
        font-weight: bold;
        margin-top: 8px;
        height: 40px;
        overflow: hidden;
    }
    .ingredient-tag {
        display: inline-block;
        background-color: #f0f2f6;
        color: #31333F;
        padding: 4px 8px;
        border-radius: 10px;
        margin: 2px;
        font-size: 11px;
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
    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?a={area}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('meals', [])
    return []

def get_meal_details(meal_id):
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
    response = requests.get(url)
    if response.status_code == 200:
        meal = response.json().get('meals', [None])[0]
        st.session_state['current_recipe'] = meal
        # Kerime lehe algusse (Streamlit reruns automaatselt)

# --- KÜLGPANEEL ---
st.sidebar.title("🍱 Menüü Seaded")

piirkond = st.sidebar.selectbox(
    "Millist maailma kööki soovid avastada?",
    ["Italian", "Mexican", "Japanese", "Chinese", "French", "Indian", "Greek", "American", "British", "Thai", "Vietnamese"]
)

if st.sidebar.button("🎲 Juhuslik üllatustoit"):
    res = requests.get("https://www.themealdb.com/api/json/v1/1/random.php").json()
    st.session_state['current_recipe'] = res['meals'][0]

st.sidebar.divider()
st.sidebar.subheader("⭐ Minu Lemmikud")
for fav in st.session_state['favorites']:
    st.sidebar.write(f"• {fav}")

if st.sidebar.button("🗑️ Tühjenda list"):
    st.session_state['favorites'] = []
    st.rerun()

# --- PEALEHT ---
st.title("🍽️ Toidukorra Planeerija")

# --- 1. OSA: VALITUD RETSEPTI DETAILID (Kuvatakse ainult siis, kui midagi on valitud) ---
if st.session_state['current_recipe']:
    recipe = st.session_state['current_recipe']
    
    with st.expander("📖 VAATA VALITUD RETSEPTTI", expanded=True):
        col_img, col_info = st.columns([1, 1.5])
        
        with col_img:
            st.image(recipe['strMealThumb'], use_container_width=True)
            if st.button("❤️ Lisa lemmikutesse", use_container_width=True):
                if recipe['strMeal'] not in st.session_state['favorites']:
                    st.session_state['favorites'].append(recipe['strMeal'])
                    st.success("Lisatud!")
        
        with col_info:
            st.header(recipe['strMeal'])
            st.write(f"**Päritolu:** {recipe['strArea']} | **Tüüp:** {recipe['strCategory']}")
            
            st.subheader("Vajalikud koostisosad:")
            # Kuvame koostisosad kenasti ritta
            for i in range(1, 21):
                ing = recipe.get(f'strIngredient{i}')
                meas = recipe.get(f'strMeasure{i}')
                if ing and ing.strip():
                    st.markdown(f'<span class="ingredient-tag">🛒 {ing} ({meas})</span>', unsafe_allow_html=True)
            
            st.subheader("Valmistamisõpetus:")
            st.write(recipe['strInstructions'])
            
            if recipe['strYoutube']:
                st.video(recipe['strYoutube'])
    
    if st.button("❌ Sule retsept"):
        st.session_state['current_recipe'] = None
        st.rerun()

st.divider()

# --- 2. OSA: VISUAALNE VALIK (Piltidega ruudustik) ---
st.subheader(f"Vali midagi head: {piirkond} köök")
meals = get_recipes_by_area(piirkond)

if meals:
    # Teeme 4 tulpa, et pilte mahuks rohkem
    cols = st.columns(4)
    
    for idx, m in enumerate(meals):
        with cols[idx % 4]:
            st.markdown(f"""
                <div class="meal-card">
                    <img src="{m['strMealThumb']}" style="width:100%; border-radius:8px;">
                    <div class="meal-title">{m['strMeal']}</div>
                </div>
            """, unsafe_allow_html=True)
            # Kasutame nuppu pildi all, et valida toit
            if st.button("Vaata retsepti", key=m['idMeal'], use_container_width=True):
                get_meal_details(m['idMeal'])
                st.rerun()
else:
    st.error("Selle piirkonna toite hetkel ei leitud.")

st.caption("Andmed pärinevad TheMealDB API-st. Head isu!")
