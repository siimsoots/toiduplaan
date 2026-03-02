import streamlit as st
import requests
import random

# --- CONFIGURATION ---
st.set_page_config(page_title="Global Chef | AI Meal Planner", layout="wide", page_icon="🍳")

# --- CSS STYLING (Professional & Visual) ---
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    .meal-card {
        background-color: white;
        padding: 0px;
        border-radius: 15px;
        border: 1px solid #eee;
        text-align: center;
        margin-bottom: 25px;
        transition: 0.4s;
        overflow: hidden;
    }
    .meal-card:hover {
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        transform: translateY(-5px);
    }
    .meal-img {
        width: 100%;
        height: 180px;
        object-fit: cover;
    }
    .meal-info {
        padding: 15px;
    }
    .meal-title {
        font-size: 16px;
        font-weight: 700;
        color: #2c3e50;
        height: 45px;
        overflow: hidden;
        margin-bottom: 10px;
    }
    .time-tag {
        font-size: 11px;
        color: #7f8c8d;
        background: #f1f2f6;
        padding: 2px 8px;
        border-radius: 10px;
        font-weight: 600;
    }
    .ingredient-chip {
        display: inline-block;
        background-color: #e8f4fd;
        color: #1a73e8;
        padding: 5px 12px;
        border-radius: 20px;
        margin: 3px;
        font-size: 12px;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'favs' not in st.session_state: st.session_state['favs'] = []
if 'recipe' not in st.session_state: st.session_state['recipe'] = None

# --- API FUNCTIONS ---
@st.cache_data
def get_meals_by_areas(areas):
    all_meals = []
    for area in areas:
        url = f"https://www.themealdb.com/api/json/v1/1/filter.php?a={area}"
        data = requests.get(url).json()
        if data.get('meals'):
            for m in data['meals']:
                m['origin'] = area # Keep track of which country it belongs to
            all_meals.extend(data['meals'])
    return all_meals

def get_details(mid):
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={mid}"
    res = requests.get(url).json()
    return res['meals'][0] if res.get('meals') else None

def estimate_time(instructions):
    # Logic: Short instructions = Fast, Long = Slow
    if not instructions: return "Medium"
    length = len(instructions)
    if length < 500: return "Fast (< 30m)"
    if length < 1000: return "Medium (30-60m)"
    return "Long (1h+)"

# --- SIDEBAR (Settings) ---
st.sidebar.title("🛠️ Planner Settings")
st.sidebar.info("Select your preferences to customize your visual menu.")

selected_areas = st.sidebar.multiselect(
    "Choose Cuisine Regions:",
    options=["Italian", "Mexican", "Japanese", "Chinese", "French", "Indian", "Greek", "American", "British", "Thai", "Spanish"],
    default=["Italian", "Mexican"]
)

meal_type = st.sidebar.radio(
    "What kind of meal?",
    ["Savory (Mains)", "Dessert", "Snacks & Sides"]
)

prep_speed = st.sidebar.multiselect(
    "Preparation Speed:",
    options=["Fast (< 30m)", "Medium (30-60m)", "Long (1h+)"],
    default=["Fast (< 30m)", "Medium (30-60m)", "Long (1h+)"]
)

if st.sidebar.button("🎲 Random Surprise Meal"):
    st.session_state['recipe'] = requests.get("https://www.themealdb.com/api/json/v1/1/random.php").json()['meals'][0]

st.sidebar.divider()
st.sidebar.subheader("⭐ Saved Favorites")
for f in st.session_state['favs']:
    st.sidebar.caption(f"❤️ {f}")

# --- MAIN PAGE ---
st.title("🍳 Global Meal Planner")
st.markdown("Discover traditional recipes from around the world. **Click a meal to see the recipe.**")

# 1. FETCH & FILTER DATA
if selected_areas:
    raw_meals = get_meals_by_areas(selected_areas)
    filtered_meals = []

    with st.spinner("Analyzing recipes..."):
        # We need to fetch details for EACH meal to filter by type/time properly
        # To keep it fast, we only process a reasonable amount (e.g. 24)
        for m in raw_meals[:40]: 
            details = get_details(m['idMeal'])
            if not details: continue
            
            # Filter by Meal Type
            cat = details.get('strCategory', '')
            if meal_type == "Dessert" and cat != "Dessert": continue
            if meal_type == "Snacks & Sides" and cat not in ["Side", "Starter"]: continue
            if meal_type == "Savory (Mains)" and cat in ["Dessert", "Side", "Starter"]: continue
            
            # Filter by Prep Time
            est = estimate_time(details.get('strInstructions', ''))
            if est not in prep_speed: continue
            
            m['details'] = details
            m['time'] = est
            filtered_meals.append(m)

    # 2. SHOW SELECTED RECIPE (TOP OVERLAY)
    if st.session_state['recipe']:
        r = st.session_state['recipe']
        with st.expander("📖 ACTIVE RECIPE: " + r['strMeal'], expanded=True):
            c1, c2 = st.columns([1, 1.2])
            with c1:
                st.image(r['strMealThumb'], use_container_width=True)
                if st.button("❤️ Add to Favorites", use_container_width=True):
                    if r['strMeal'] not in st.session_state['favs']:
                        st.session_state['favs'].append(r['strMeal'])
            with c2:
                st.header(r['strMeal'])
                st.write(f"**Origin:** {r.get('strArea')} | **Category:** {r.get('strCategory')}")
                st.subheader("Shopping List")
                for i in range(1, 21):
                    ing = r.get(f'strIngredient{i}')
                    msr = r.get(f'strMeasure{i}')
                    if ing and ing.strip():
                        st.markdown(f'<span class="ingredient-chip">{ing} ({msr})</span>', unsafe_allow_html=True)
                st.subheader("Instructions")
                st.write(r['strInstructions'])
                if st.button("Close Recipe"):
                    st.session_state['recipe'] = None
                    st.rerun()

    # 3. VISUAL GRID
    st.divider()
    if filtered_meals:
        cols = st.columns(4)
        for idx, meal in enumerate(filtered_meals):
            with cols[idx % 4]:
                st.markdown(f"""
                    <div class="meal-card">
                        <img src="{meal['strMealThumb']}" class="meal-img">
                        <div class="meal-info">
                            <div class="meal-title">{meal['strMeal']}</div>
                            <span class="time-tag">⏱️ {meal['time']}</span>
                            <div style="font-size: 10px; color: #aaa; margin-top: 5px;">{meal['origin']} Cuisine</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("View Recipe", key=meal['idMeal'], use_container_width=True):
                    st.session_state['recipe'] = meal['details']
                    st.rerun()
    else:
        st.warning("No matches found for your current filters. Try selecting more regions or speeds.")
else:
    st.info("Please select at least one region in the sidebar to begin.")

st.sidebar.caption("Data powered by TheMealDB API")
