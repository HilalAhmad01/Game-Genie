import google.generativeai as genai
import requests
import streamlit as st
from PIL import Image

# Replace with your Gemini API key
GEMINI_API_KEY = "AIzaSyCJa8romWJXguSljx3j4V5Wv2Mjf_Gl1EQ"
genai.configure(api_key=GEMINI_API_KEY)

# Replace with your RAWG API key
RAWG_API_KEY = "d10ba5f2f4ee488ab1da0ae6ae53267e"

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-2.0-flash')

# Streamlit Frontend
st.title("🎮 GameGenie: Your Personal Game Recommender")

# Custom Bot Personality
BOT_NAME = "GameGenie"
BOT_PERSONALITY = "friendly, enthusiastic, and knowledgeable about video games"
BOT_PROFILE_PIC = Image.open("gamegenie_profile.jpg")  # Replace with your image file

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"], avatar=BOT_PROFILE_PIC if message["role"] == "assistant" else None):
        st.write(message["content"])

def get_rawg_game_details(game_name):
    """
    Fetch game details from the RAWG API using the game name.
    """
    search_url = f"https://api.rawg.io/api/games?key={RAWG_API_KEY}&search={game_name}"
    response = requests.get(search_url)
    if response.status_code == 200:
        games = response.json()["results"]
        if games:
            return games[0]  # Return the first match
    return None

user_input = st.chat_input(f"Hey there! Describe the type of game you want to play (e.g., 'I want a multiplayer shooter game for PC'):")

if user_input:
    # Add user input to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Generate a response using Gemini
    prompt = f"""
    You are {BOT_NAME}, a friendly video game recommendation chatbot with a {BOT_PERSONALITY} personality. 
    The user has described the type of game they want to play. 
    Recommend 5 games that match their preferences. Return only the game names, separated by commas.
    User's input: {user_input}
    """
    with st.spinner(f"{BOT_NAME} is thinking..."):
        response = model.generate_content(prompt)

    # Add bot response to chat history
    st.session_state.chat_history.append({"role": "assistant", "content": f"Here are some games you might like:"})
    with st.chat_message("assistant", avatar=BOT_PROFILE_PIC):
        st.write("Here are some games you might like:")
         # Step 3: Fetch RAWG details for each recommended game
    recommended_games = response.text.split(",")  # Split response into individual game names
    for game in recommended_games:
        game = game.strip()  # Remove extra spaces
        with st.spinner(f"Fetching details for **{game}**..."):
            # Fetch RAWG details
            rawg_details = get_rawg_game_details(game)
            if rawg_details:
                # Display game details in a card-like format
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.image(rawg_details.get("background_image", "https://via.placeholder.com/300x150"), width=200)
                    with col2:
                        st.write(f"**{rawg_details.get('name', 'N/A')}**")
                        st.write(f"**Release Date:** {rawg_details.get('released', 'N/A')}")
                        st.write(f"**Rating:** {rawg_details.get('rating', 'N/A')}")
                        st.write(f"**Description:** {rawg_details.get('description_raw', 'N/A')}")
                        st.write(f"**Genres:** {', '.join([genre['name'] for genre in rawg_details.get('genres', [])])}")
                        st.write(f"**RAWG Store:** [Link]({rawg_details.get('website', '#')})")
                st.write("---")
            else:
                st.write(f"Sorry, I couldn't find details for **{game}** on RAWG.")
                st.write("---")

# Reset Chat Button
if st.button("Reset Chat"):
    st.session_state.chat_history = []
    st.experimental_rerun()

# Footer
st.markdown("---")
st.markdown("Made with ❤️ by Hilal Ahmad | Powered by [Gemini](https://ai.google.dev/) and [RAWG](https://rawg.io/)")
