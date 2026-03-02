import streamlit as st
import requests
import random
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="Global Chef | Universal Recipe Engine", layout="wide", page_icon="👨‍🍳")

# --- CSS STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .meal-card {
        background-color: white;
        border-radius: 15px;
        border: 1px solid #ddd;
        text-align: center;
        margin-bottom: 20px;
        overflow: hidden;
        transition: 0.3s;
    }
    .meal-card:hover {
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        transform: translateY(-3px);
    }
    .meal-img { width: 100%; height: 160px; object-fit: cover; }
    .meal-info { padding: 12px; }
    .meal-title { font-size: 15px; font-weight: bold; height: 40px; overflow: hidden; color: #2c3e50; }
    .user-tag { background-color: #ff4b4b; color: white; padding: 2px 6px; border-radius: 5px; font-size: 10px; }
    .api-tag { background-color: #1a73e8; color: white; padding: 2px 6px; border-radius: 5px; font-size: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'user_meals' not in st.session_state: st.session_state['user_meals'] = []
if 'current_recipe' not in st.session_state: st.session_state['current_recipe'] = None
if 'shuffled_indices' not in st.session_state: st.session_state['shuffled_indices'] = []

# --- FUNCTIONS ---
def get_meals(areas):
    all_meals = []
    for area in areas:
        url = f"https://www.themealdb.com/api/json/v1/1/filter.php?a={area}"
        data = requests.get(url).json()
        if data.get('meals'):
            for m in data['meals']:
                m['origin'] = area
                m['is_user'] = False
                all_meals.append(m)
    return all_meals

def get_details(mid):
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={mid}"
    res = requests.get(url).json()
    return res['meals'][0] if res.get('meals') else None

def search_meal(query):
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={query}"
    res = requests.get(url).json()
    return res['meals'] if res.get('meals') else []

# --- SIDEBAR: ADD YOUR OWN RECIPE ---
st.sidebar.title("✍️ My Cookbook")
with st.sidebar.expander("➕ Add Your Own Recipe"):
    u_name = st.text_input("Meal Name")
    u_cat = st.selectbox("Category", ["Savory", "Dessert", "Snack"])
    u_ins = st.text_area("Instructions")
    u_ing = st.text_area("Ingredients (comma separated)")
    u_img = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
    
    if st.button("Save My Recipe"):
        if u_name and u_ins:
            new_meal = {
                'strMeal': u_name,
                'strMealThumb': u_img if u_img else "https://via.placeholder.com/300?text=My+Recipe",
                'strInstructions': u_ins,
                'ingredients': u_ing,
                'strCategory': u_cat,
                'strArea': "Personal",
                'is_user': True,
                'idMeal': f"user_{random.randint(1000, 9999)}"
            }
            st.session_state['user_meals'].append(new_meal)
            st.success("Recipe added to menu!")
        else:
            st.error("Please provide a name and instructions.")

# --- SIDEBAR: SETTINGS ---
st.sidebar.title("⚙️ Filters")
selected_areas = st.sidebar.multiselect(
    "Regions", 
    ["Italian", "Mexican", "Japanese", "Chinese", "French", "Indian", "Greek", "American", "British", "Thai", "Spanish"],
    default=["Italian", "Mexican"]
)
meal_type = st.sidebar.radio("Type", ["Savory", "Dessert", "Snack"])

# --- MAIN PAGE ---
st.title("🌎 Universal Meal Planner")

# Search & Refresh Row
col_search, col_ref = st.columns([3, 1])
with col_search:
    query = st.text_input("🔍 Search for any dish globally (e.g. 'Pasta', 'Curry', 'Cake')...")
with col_ref:
    st.write(" ") # alignment
    refresh = st.button("🔄 Refresh & Discover", use_container_width=True)

# 1. DATA PROCESSING
display_list = []

if query:
    # Use Search Results
    search_results = search_meal(query)
    for m in search_results:
        m['is_user'] = False
        m['origin'] = m.get('strArea', 'World')
        display_list.append(m)
else:
    # Use Region + User Meals
    api_meals = get_meals(selected_areas)
    # Combine with user-added meals
    all_combined = st.session_state['user_meals'] + api_meals
    
    # Filter by category (User meals have category, API meals need details fetch)
    filtered = []
    for m in all_combined:
        if m['is_user']:
            if m['strCategory'] == meal_type: filtered.append(m)
        else:
            filtered.append(m) # We filter API meals after shuffle for performance
    
    # SHUFFLE LOGIC: If refresh or first run, pick 12 random items
    if refresh or not st.session_state['shuffled_indices']:
        random.shuffle(filtered)
        display_list = filtered[:20]
    else:
        display_list = filtered[:20]

# 2. ACTIVE RECIPE DISPLAY
if st.session_state['current_recipe']:
    r = st.session_state['current_recipe']
    with st.expander("📖 VIEWING RECIPE: " + r['strMeal'], expanded=True):
        c1, c2 = st.columns([1, 1.2])
        with c1:
            if isinstance(r['strMealThumb'], str):
                st.image(r['strMealThumb'], use_container_width=True)
            else:
                st.image(r['strMealThumb'], use_container_width=True)
        with c2:
            st.header(r['strMeal'])
            st.write(f"**Origin:** {r.get('strArea')} | **Source:** {'User' if r['is_user'] else 'TheMealDB'}")
            st.subheader("Instructions")
            st.write(r['strInstructions'])
            if st.button("Close Recipe"):
                st.session_state['current_recipe'] = None
                st.rerun()

st.divider()

# 3. VISUAL GRID
if display_list:
    cols = st.columns(4)
    for idx, meal in enumerate(display_list):
        with cols[idx % 4]:
            tag = '<span class="user-tag">PERSONAL</span>' if meal['is_user'] else f'<span class="api-tag">{meal["origin"]}</span>'
            
            st.markdown(f"""
                <div class="meal-card">
                    <div class="meal-info" style="position:absolute; padding:5px;">{tag}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Image handling for both URLs and Uploads
            if isinstance(meal['strMealThumb'], str):
                st.image(meal['strMealThumb'], use_container_width=True)
            else:
                st.image(meal['strMealThumb'], use_container_width=True)
            
            st.markdown(f'<div class="meal-title">{meal["strMeal"]}</div>', unsafe_allow_html=True)
            
            if st.button("View Details", key=meal['idMeal'], use_container_width=True):
                if meal['is_user']:
                    st.session_state['current_recipe'] = meal
                else:
                    st.session_state['current_recipe'] = get_details(meal['idMeal'])
                st.rerun()
else:
    st.warning("No recipes found. Try clicking 'Refresh' or changing your filters.")
