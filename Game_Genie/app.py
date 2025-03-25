# MUST BE THE FIRST LINE - PAGE CONFIG
import streamlit as st
st.set_page_config(page_title="GameGenie", page_icon="🎮", layout="wide")

# Now import other libraries
import pickle
import pandas as pd
import requests
import google.generativeai as genai
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from PIL import Image
from io import BytesIO
import os

# ===== DATA LOADING =====
def load_game_data():
    """Safe data loading with all error handling"""
    try:
        # Load games list
        if os.path.exists('games_list.pkl'):
            with open('games_list.pkl', 'rb') as f:
                games_data = pickle.load(f)
                if isinstance(games_data, list):
                    games_df = pd.DataFrame(games_data)
                elif isinstance(games_data, pd.DataFrame):
                    games_df = games_data
                else:
                    st.error("Invalid games data format")
                    return None, None
        
        # Load or compute similarity
        if os.path.exists('similarity.pkl'):
            with open('similarity.pkl', 'rb') as f:
                similarity = pickle.load(f)
        else:
            st.warning("Computing similarity matrix...")
            cv = CountVectorizer(max_features=5000, stop_words='english')
            vectors = cv.fit_transform(games_df['game_tags'])
            similarity = cosine_similarity(vectors)
            with open('similarity.pkl', 'wb') as f:
                pickle.dump(similarity, f)
        
        return games_df, similarity
    
    except Exception as e:
        st.error(f"Data loading failed: {str(e)}")
        return None, None

games_df, similarity = load_game_data()

# ===== API SETUP =====
try:
    genai.configure(api_key="Your_Gemini_API_Key_here")
    model = genai.GenerativeModel('gemini-2.0-flash')
    RAWG_API_KEY = "Your_Rawg_Api_Key_here"
except Exception as e:
    st.error(f"API setup failed: {str(e)}")
    st.stop()

# ===== CORE FUNCTIONS =====
def get_game_details(name):
    """Get game details from RAWG API"""
    try:
        response = requests.get(
            "https://api.rawg.io/api/games",
            params={"key": RAWG_API_KEY, "search": name, "page_size": 1},
            timeout=10
        )
        if response.status_code == 200 and response.json()['results']:
            return response.json()['results'][0]
        return None
    except:
        return None

def show_game(game):
    """Display game card"""
    if not game:
        return
    
    with st.container():
        cols = st.columns([1, 3])
        with cols[0]:
            img_url = game.get('background_image', '')
            try:
                if img_url:
                    img = Image.open(BytesIO(requests.get(img_url, timeout=5).content))
                    st.image(img, width=150)
                else:
                    st.image("https://via.placeholder.com/150x200?text=No+Image", width=150)
            except:
                st.image("https://via.placeholder.com/150x200?text=No+Image", width=150)
        
        with cols[1]:
            st.subheader(game.get('name', 'Unknown'))
            if game.get('rating'):
                st.write(f"⭐ Rating: {game['rating']:.1f}/5")
            if game.get('released'):
                st.write(f"📅 Released: {game['released']}")
            if game.get('genres'):
                genres = ', '.join([g['name'] for g in game['genres']])
                st.write(f"🎮 Genres: {genres}")

# ===== RECOMMENDER SYSTEM =====
def find_similar_games(query):
    """Find similar games using similarity matrix"""
    if games_df is None or similarity is None:
        return None, "System not ready"
    
    matches = games_df[games_df['name'].str.contains(query, case=False)]
    if matches.empty:
        return None, "Game not found"
    
    idx = matches.index[0]
    sim_scores = list(enumerate(similarity[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:6]
    
    results = []
    for i, _ in sim_scores:
        game = games_df.iloc[i].to_dict()
        details = get_game_details(game['name'])
        results.append(details or game)
    
    return results, None

# ===== CHATBOT SYSTEM =====
def get_ai_recommendations(query):
    """Get recommendations from Gemini"""
    try:
        response = model.generate_content(
            f"Recommend 3 games matching: '{query}'. Return ONLY comma-separated names."
        )
        names = [n.strip() for n in response.text.split(",") if n.strip()][:3]
        return names
    except:
        return None

# ===== MAIN APP =====
st.title("🎮 GameGenie")

tab1, tab2 = st.tabs(["🔍 Game Recommender", "💬 AI Assistant"])

with tab1:
    st.header("Find Similar Games")
    if games_df is None:
        st.error("Game data not loaded")
    else:
        query = st.text_input("Enter a game you like:")
        if query:
            games, error = find_similar_games(query)
            if error:
                st.error(error)
            elif games:
                st.success("Recommended games:")
                for game in games:
                    show_game(game)

with tab2:
    st.header("AI Game Recommender")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "games" in msg:
                for game in msg["games"]:
                    show_game(game)
    
    if prompt := st.chat_input("Describe your ideal game"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                game_names = get_ai_recommendations(prompt)
                if game_names:
                    st.write("Recommended games:")
                    games = []
                    for name in game_names:
                        details = get_game_details(name)
                        if details:
                            show_game(details)
                            games.append(details)
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "Here are my recommendations:",
                        "games": games
                    })
                else:
                    st.write("Sorry, I couldn't find matches. Try being more specific.")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "No matches found"
                    })

st.caption("Game recommendation system powered by RAWG API and Gemini AI")