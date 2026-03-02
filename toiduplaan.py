import streamlit as st
import requests
import random

# --- CONFIGURATION ---
st.set_page_config(page_title="Culinary Planner Pro", layout="wide")

# --- VISUAL THEME (White Background, Dark Text) ---
st.markdown("""
    <style>
    /* White Main Background */
    .stApp {
        background-color: #ffffff;
        color: #1a1a1a;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
        border-right: 1px solid #ddd;
    }
    
    /* Ensure all text in sidebar and main area is dark */
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p,
    h1, h2, h3, p, span {
        color: #1a1a1a !important;
    }

    /* Professional Meal Cards */
    .meal-card {
        background-color: #ffffff;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 20px;
        overflow: hidden;
        border: 1px solid #eee;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        height: 100%;
        color: #1a1a1a;
    }
    
    .meal-img { 
        width: 100%; 
        height: 220px; 
        object-fit: cover; 
    }
    
    .meal-info { 
        padding: 15px; 
    }
    
    .meal-title { 
        font-family: 'Helvetica', sans-serif;
        font-size: 15px; 
        font-weight: 800; 
        color: #000000; 
        margin-bottom: 10px;
        min-height: 45px;
        text-transform: uppercase;
    }
    
    .tag-line {
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #777;
        border-top: 1px solid #eee;
        padding-top: 10px;
    }

    /* BUTTONS STYLING - Ensuring visibility */
    .stButton>button {
        background-color: #ffffff !important;
        color: #1a1a1a !important; /* Force dark text */
        border: 1px solid #cccccc !important;
        border-radius: 4px !important;
        font-weight: bold !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease;
    }

    .stButton>button:hover {
        background-color: #f0f2f6 !important;
        border-color: #1a1a1a !important;
    }

    /* Input field text visibility */
    input {
        color: #1a1a1a !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'seen_recipes' not in st.session_state: st.session_state['seen_recipes'] = set()
if 'current_pool' not in st.session_state: st.session_state['current_pool'] = []
if 'user_recipes' not in st.session_state: st.session_state['user_recipes'] = []
if 'selected_meal' not in st.session_state: st.session_state['selected_meal'] = None
if 'favorites' not in st.session_state: st.session_state['favorites'] = []

# --- CORE FUNCTIONS ---
def fetch_meals_by_regions(regions):
    pool = []
    for region in regions:
        url = f"https://www.themealdb.com/api/json/v1/1/filter.php?a={region}"
        try:
            response = requests.get(url).json()
            if response['meals']:
                for m in response['meals']:
                    m['region_name'] = region
                    pool.append(m)
        except:
            continue
    return pool

def get_full_details(meal_id):
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
    res = requests.get(url).json()
    return res['meals'][0] if res['meals'] else None

def analyze_time(instructions):
    if not instructions: return "Medium (30-60m)"
    length = len(instructions)
    if length < 500: return "Fast (< 30m)"
    if length < 1200: return "Medium (30-60m)"
    return "Long (1h+)"

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.header("Recipe Controls")
    
    # 1. Favorites List
    st.subheader("Saved Favorites")
    if st.session_state['favorites']:
        for idx, fav in enumerate(st.session_state['favorites']):
            if st.button(f"View: {fav['strMeal']}", key=f"fav_{idx}", use_container_width=True):
                st.session_state['selected_meal'] = fav
                st.rerun()
        if st.button("Clear Favorites", key="clear_favs"):
            st.session_state['favorites'] = []
            st.rerun()
    else:
        st.write("No favorites saved yet.")
    
    st.divider()

    # 2. Add Custom Dish
    with st.expander("Add Custom Dish"):
        c_name = st.text_input("Name")
        c_type = st.selectbox("Category", ["Savory", "Dessert", "Snack"])
        c_time = st.selectbox("Time", ["Fast (< 30m)", "Medium (30-60m)", "Long (1h+)"])
        c_steps = st.text_area("Steps")
        c_img = st.file_uploader("Photo", type=["jpg", "png"])
        
        if st.button("Add to My List"):
            if c_name and c_steps:
                st.session_state['user_recipes'].append({
                    'strMeal': c_name,
                    'strMealThumb': c_img if c_img else "https://via.placeholder.com/400",
                    'strInstructions': c_steps,
                    'strCategory': c_type,
                    'prep_time': c_time,
                    'strArea': "Personal",
                    'idMeal': f"custom_{random.randint(1000,9999)}"
                })
                st.success("Dish added.")

    st.divider()

    # 3. Filter System
    st.subheader("Filter Selection")
    regions = st.multiselect(
        "Cuisine Origin",
        ["Italian", "Mexican", "Japanese", "Chinese", "French", "Indian", "Greek", "American", "British", "Thai", "Spanish", "Moroccan"],
        default=["Italian", "Mexican"]
    )
    
    m_type = st.radio("Course Type", ["Savory", "Dessert", "Snack"])
    
    speeds = st.multiselect(
        "Preparation Time",
        ["Fast (< 30m)", "Medium (30-60m)", "Long (1h+)"],
        default=["Fast (< 30m)", "Medium (30-60m)", "Long (1h+)"]
    )

    st.divider()
    apply_filters = st.button("Apply Filters & Search", use_container_width=True)

# --- MAIN PAGE CONTENT ---
st.title("Culinary Planner")
st.write("Professional meal planning and global recipe discovery.")

# Top Search/Refresh Row
col_1, col_2 = st.columns([3, 1])
with col_1:
    search_input = st.text_input("Search global database for ingredients or dishes...")
with col_2:
    st.write(" ")
    refresh_button = st.button("Refresh Results", use_container_width=True)

# PROCESSING LOGIC
if apply_filters or refresh_button or not st.session_state['current_pool']:
    results = []
    
    if search_input:
        search_res = requests.get(f"https://www.themealdb.com/api/json/v1/1/search.php?s={search_input}").json()
        raw_list = search_res['meals'] if search_res['meals'] else []
    else:
        # Use regions + user recipes
        raw_list = st.session_state['user_recipes'] + fetch_meals_by_regions(regions)
        random.shuffle(raw_list)

    # Filter and validate
    for item in raw_list:
        if item['idMeal'] in st.session_state['seen_recipes'] and not search_input:
            continue
        
        if 'strInstructions' not in item:
            full_data = get_full_details(item['idMeal'])
            if not full_data: continue
            item.update(full_data)

        # Apply Filters
        cat = item.get('strCategory', '')
        if m_type == "Dessert" and cat != "Dessert": continue
        if m_type == "Snack" and cat not in ["Side", "Starter"]: continue
        if m_type == "Savory" and cat in ["Dessert", "Side", "Starter"]: continue
        
        item['prep_time'] = analyze_time(item.get('strInstructions', ''))
        if item['prep_time'] not in speeds: continue
        
        results.append(item)
        st.session_state['seen_recipes'].add(item['idMeal'])
        
        if len(results) >= 12: break

    st.session_state['current_pool'] = results

# DISPLAY DETAIL VIEW
if st.session_state['selected_meal']:
    meal = st.session_state['selected_meal']
    with st.container():
        st.divider()
        st.header(meal['strMeal'])
        c1, c2 = st.columns([1, 2])
        with c1:
            st.image(meal['strMealThumb'], use_container_width=True)
            # Favorite Button
            if st.button("Add to Favorites"):
                if meal['idMeal'] not in [f['idMeal'] for f in st.session_state['favorites']]:
                    st.session_state['favorites'].append(meal)
                    st.success("Saved to favorites.")
            
            if st.button("Close Selection"):
                st.session_state['selected_meal'] = None
                st.rerun()
        with c2:
            st.write(f"**Region:** {meal.get('strArea')} | **Time:** {meal.get('prep_time')}")
            st.subheader("Ingredients")
            ings = [f"{meal.get(f'strMeasure{i}')} {meal.get(f'strIngredient{i}')}" for i in range(1, 21) if meal.get(f'strIngredient{i}')]
            st.write(", ".join(ings))
            st.subheader("Instructions")
            st.write(meal.get('strInstructions'))
    st.divider()

# DISPLAY MENU GRID
if st.session_state['current_pool']:
    cols = st.columns(4)
    for idx, meal in enumerate(st.session_state['current_pool']):
        with cols[idx % 4]:
            st.markdown(f"""
                <div class="meal-card">
                    <img src="{meal['strMealThumb']}" class="meal-img">
                    <div class="meal-info">
                        <div class="meal-title">{meal['strMeal']}</div>
                        <div class="tag-line">
                            {meal.get('strArea')} | {meal.get('prep_time')}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("View Details", key=meal['idMeal'], use_container_width=True):
                st.session_state['selected_meal'] = meal
                st.rerun()
else:
    st.info("No dishes found. Adjust filters or regions to see more options.")

st.markdown("<br><br><p style='text-align: center; color: #999; font-size: 11px;'>Global Recipe Discovery Engine</p>", unsafe_allow_html=True)
