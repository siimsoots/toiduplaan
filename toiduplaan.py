import streamlit as st
import requests
import random

# --- CONFIGURATION ---
st.set_page_config(page_title="Culinary Journey", layout="wide")

# --- CUSTOM THEME & VISUALS (Cozy Red & White Sidebar) ---
st.markdown("""
    <style>
    /* Cozy Red Background */
    .stApp {
        background: linear-gradient(135deg, #7b1113 0%, #a21c1e 100%);
        color: white;
    }
    
    /* White Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #ddd;
    }
    
    /* Sidebar Text Color */
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label {
        color: #333 !important;
    }

    /* Professional Meal Cards */
    .meal-card {
        background-color: white;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 25px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        height: 100%;
        color: #333;
    }
    
    .meal-img { 
        width: 100%; 
        height: 200px; 
        object-fit: cover; 
    }
    
    .meal-info { 
        padding: 15px; 
    }
    
    .meal-title { 
        font-family: 'Georgia', serif;
        font-size: 18px; 
        font-weight: bold; 
        color: #7b1113; 
        margin-bottom: 10px;
        min-height: 50px;
    }
    
    .tag-box {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #888;
        border-top: 1px solid #eee;
        padding-top: 10px;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 4px;
        border: none;
        transition: 0.3s;
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Georgia', serif;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE FOR REFRESH LOGIC ---
if 'seen_recipes' not in st.session_state:
    st.session_state['seen_recipes'] = set()
if 'current_pool' not in st.session_state:
    st.session_state['current_pool'] = []
if 'user_recipes' not in st.session_state:
    st.session_state['user_recipes'] = []
if 'selected_meal' not in st.session_state:
    st.session_state['selected_meal'] = None

# --- API LOGIC ---
def fetch_all_potential_meals(areas):
    pool = []
    for area in areas:
        url = f"https://www.themealdb.com/api/json/v1/1/filter.php?a={area}"
        try:
            data = requests.get(url).json()
            if data['meals']:
                for m in data['meals']:
                    m['area'] = area
                    pool.append(m)
        except:
            continue
    return pool

def get_meal_details(meal_id):
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
    res = requests.get(url).json()
    return res['meals'][0] if res['meals'] else None

def estimate_prep_time(instructions):
    if not instructions: return "Medium"
    length = len(instructions)
    if length < 500: return "Fast (< 30m)"
    if length < 1100: return "Medium (30-60m)"
    return "Long (1h+)"

# --- SIDEBAR CONTENT ---
with st.sidebar:
    st.title("Menu Designer")
    
    # 1. Add Personal Recipe
    with st.expander("Contribute a Recipe"):
        new_name = st.text_input("Dish Name")
        new_type = st.selectbox("Category", ["Savory", "Dessert", "Snack"])
        new_time = st.selectbox("Time Needed", ["Fast (< 30m)", "Medium (30-60m)", "Long (1h+)"])
        new_ins = st.text_area("Cooking Steps")
        new_img = st.file_uploader("Dish Photo", type=["jpg", "png"])
        
        if st.button("Save to My Collection"):
            if new_name and new_ins:
                recipe = {
                    'strMeal': new_name,
                    'strMealThumb': new_img if new_img else "https://via.placeholder.com/300",
                    'strInstructions': new_ins,
                    'strCategory': new_type,
                    'prep_time': new_time,
                    'strArea': "Personal",
                    'idMeal': f"custom_{random.randint(100,999)}"
                }
                st.session_state['user_recipes'].append(recipe)
                st.success("Recipe saved!")

    st.divider()
    
    # 2. Filters
    st.subheader("Preferences")
    selected_areas = st.multiselect(
        "Cuisine Origin",
        ["Italian", "Mexican", "Japanese", "Chinese", "French", "Indian", "Greek", "American", "British", "Thai", "Spanish", "Moroccan"],
        default=["Italian", "Mexican", "French"]
    )
    
    selected_type = st.radio("Course Type", ["Savory", "Dessert", "Snack"])
    
    selected_speeds = st.multiselect(
        "Preparation Time",
        ["Fast (< 30m)", "Medium (30-60m)", "Long (1h+)"],
        default=["Fast (< 30m)", "Medium (30-60m)", "Long (1h+)"]
    )

# --- MAIN INTERFACE ---
st.title("The Culinary Planner")
st.write("Browse unique recipes from around the world. Every refresh brings new inspiration.")

# Search and Refresh functionality
col_a, col_b = st.columns([3, 1])
with col_a:
    search_q = st.text_input("Search the entire global database (e.g. 'Salmon', 'Pasta', 'Curry')...")
with col_b:
    st.write(" ")
    refresh_clicked = st.button("Generate New Menu", use_container_width=True)

# LOGIC: Fetching and Novelty filtering
if refresh_clicked or not st.session_state['current_pool']:
    new_display_list = []
    
    if search_q:
        search_url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={search_q}"
        search_res = requests.get(search_url).json()
        raw_list = search_res['meals'] if search_res['meals'] else []
    else:
        # Get all meals from API for selected areas + personal recipes
        raw_list = st.session_state['user_recipes'] + fetch_all_potential_meals(selected_areas)
        random.shuffle(raw_list)

    # Filtering for novelty and criteria
    for m in raw_list:
        if m['idMeal'] in st.session_state['seen_recipes'] and not search_q:
            continue # Skip if already seen recently
        
        # Get full details
        if 'strInstructions' not in m: # If it's from API and we don't have details yet
            det = get_meal_details(m['idMeal'])
            if not det: continue
            m.update(det)

        # Apply Filters
        cat = m.get('strCategory', '')
        if selected_type == "Dessert" and cat != "Dessert": continue
        if selected_type == "Snack" and cat not in ["Side", "Starter"]: continue
        if selected_type == "Savory" and cat in ["Dessert", "Side", "Starter"]: continue
        
        m['prep_time'] = estimate_prep_time(m.get('strInstructions', ''))
        if m['prep_time'] not in selected_speeds: continue
        
        new_display_list.append(m)
        st.session_state['seen_recipes'].add(m['idMeal'])
        
        if len(new_display_list) >= 12: break # Show 12 items

    st.session_state['current_pool'] = new_display_list

# DISPLAY: Selected Recipe Detail
if st.session_state['selected_meal']:
    meal = st.session_state['selected_meal']
    with st.container():
        st.markdown(f"### {meal['strMeal']}")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.image(meal['strMealThumb'], use_container_width=True)
        with c2:
            st.write(f"**Origin:** {meal.get('strArea')} | **Time:** {meal.get('prep_time')}")
            st.write("**Ingredients:**")
            # Cleaning ingredients list
            ing_list = []
            for i in range(1, 21):
                ing = meal.get(f'strIngredient{i}')
                if ing: ing_list.append(ing)
            st.write(", ".join(ing_list))
            st.write("**Preparation:**")
            st.write(meal.get('strInstructions'))
            if st.button("Close Recipe"):
                st.session_state['selected_meal'] = None
                st.rerun()
    st.divider()

# DISPLAY: The Menu Grid
if st.session_state['current_pool']:
    cols = st.columns(4)
    for idx, meal in enumerate(st.session_state['current_pool']):
        with cols[idx % 4]:
            st.markdown(f"""
                <div class="meal-card">
                    <img src="{meal['strMealThumb']}" class="meal-img">
                    <div class="meal-info">
                        <div class="meal-title">{meal['strMeal']}</div>
                        <div class="tag-box">
                            {meal.get('strArea')} &middot; {meal.get('prep_time')}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("View Full Recipe", key=meal['idMeal'], use_container_width=True):
                st.session_state['selected_meal'] = meal
                st.rerun()
else:
    st.info("Try selecting more regions or reset filters to see more dishes.")

# Footer
st.markdown("<br><hr><center>Global Culinary Database Access</center>", unsafe_allow_html=True)
