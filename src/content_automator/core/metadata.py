# generate_metadata.py

from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from typing import Dict, Optional, List
from utils.general import log_info, log_warning, log_error

# Simple mapping of game codes to titles
GAME_CODES = {
    "ZEOW": "The Legend of Zelda: Echoes of Wisdom",
    "PKMSL": "Pokemon Scarlet",
    "PKMNV": "Pokemon Violet",
    "TOTK": "The Legend of Zelda: Tears of the Kingdom",
    "BOTW": "The Legend of Zelda: Breath of the Wild",
    "MLBS": "Mario & Luigi: Brothership"
    # Add more game codes as needed
}

# Channel-specific templates
CHANNEL_TEMPLATES = {
    'VGO': {
        'title_format': "{title} - Stream Archive [{date}]",
        'description_format': """
{attention_summary}

{content_paragraph}

{subscribe_catch} 🎮

💫 Connect With Me:
Missed the live stream? Head over to: @vglevelup_
🎮 Twitch: https://www.twitch.tv/vglevelup
🔑 Discord: https://discord.gg/Xfcysgn3jU
☕ Support Me: https://www.buymeacoffee.com/vglevelup

{final_catch}
{hashtags}

💡 Share Your Thoughts:
{comment_call}
Remember, this is a stream archive - catch us live next time!""",
        'default_tags': ["VgOffline"]
    },
    'VGL': {
        'title_format': "{title} - Live Playthrough",
        'description_format': """
{attention_summary}

{content_paragraph}

{subscribe_catch} 🎮

Join us live on this channel for more adventures! 🎯

💫 Connect With Me:
For the highlights and more, visit: @vglevelup
🎮 Twitch: https://www.twitch.tv/vglevelup
🔑 Discord: https://discord.gg/Xfcysgn3jU
☕ Support Me: https://www.buymeacoffee.com/vglevelup

{final_catch}
{hashtags}

💡 Your Insights:
{comment_call}
Stay tuned for more exciting adventures ahead!""",
        'default_tags': []
    },
    'BBG': {
        'title_format': "{title} - Gameplay Walkthrough",
        'description_format': """
{attention_summary}

{content_paragraph}

{subscribe_catch} 🎮

🎮 Twitch: https://www.twitch.tv/vglevelup
🔑 Discord: https://discord.gg/Xfcysgn3jU
☕ Support Me: https://www.buymeacoffee.com/vglevelup

{final_catch}
{hashtags}

🔗 Connect with us:
For compact content 👉 @babloplus
For even more! 👉 @bablo_

More adventures coming your way! Stay tuned! 🎮""",
        'default_tags': []
    },
    'BBP': {
        'title_format': "{title}",
        'description_format': """
{attention_summary}

{subscribe_catch} 🎮

{content_paragraph}

🎮 Twitch: https://www.twitch.tv/vglevelup
🔑 Discord: https://discord.gg/Xfcysgn3jU
☕ Support Me: https://www.buymeacoffee.com/vglevelup

{final_catch}
{hashtags}

More adventures await! Don't miss out! 🎮""",
        'default_tags': []
    }
}

def setup_ollama_model(context_length: int = 12196) -> OllamaLLM:
    """Initialize the Ollama model with optimal parameters."""
    return OllamaLLM(
        model="gemma2:9b",
        temperature=0.7,
        top_k=50,
        top_p=0.9,
        repeat_penalty=1.1,
        mirostat=2,
        mirostat_eta=0.1,
        mirostat_tau=5.0,
        num_ctx=context_length,
        num_gpu=1,
        num_thread=8,
        verbose=True
    )

# def find_game_urls(game_title: str) -> Dict[str, str]:
#     """
#     Dynamically find URLs for a game by searching online with improved parsing.
#     """
#     urls = {}
    
#     try:
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
#             'Accept-Language': 'en-US,en;q=0.5',
#             'Accept-Encoding': 'gzip, deflate, br',
#             'DNT': '1',
#             'Connection': 'keep-alive',
#             'Upgrade-Insecure-Requests': '1',
#             'Sec-Fetch-Dest': 'document',
#             'Sec-Fetch-Mode': 'navigate',
#             'Sec-Fetch-Site': 'none',
#             'Sec-Fetch-User': '?1',
#             'Cache-Control': 'max-age=0'
#         }
        
#         # First try: Direct Nintendo search
#         nintendo_search = quote(f"{game_title} site:nintendo.com")
#         response = requests.get(
#             f"https://www.google.com/search?q={nintendo_search}",
#             headers=headers,
#             timeout=10
#         )
        
#         if response.status_code == 200:
#             soup = BeautifulSoup(response.text, 'html.parser')
#             # Look for search results
#             search_results = soup.find_all('div', class_='g')
#             if not search_results:
#                 # Try alternate class names
#                 search_results = soup.find_all('div', class_='yuRUbf')
            
#             # Print for debugging
#             log_info(f"Found {len(search_results)} search results for Nintendo")
            
#             for result in search_results:
#                 # Try different ways to find the URL
#                 link = result.find('a')
#                 if link and 'href' in link.attrs:
#                     url = link['href']
#                     if 'nintendo.com' in url and '/games/' in url:
#                         urls['official_url'] = url
#                         break
        
#         # Second try: Wiki/Fandom search
#         wiki_search = quote(f"{game_title} game site:zelda.fandom.com OR site:wikipedia.org")
#         response = requests.get(
#             f"https://www.google.com/search?q={wiki_search}",
#             headers=headers,
#             timeout=10
#         )
        
#         if response.status_code == 200:
#             soup = BeautifulSoup(response.text, 'html.parser')
#             search_results = soup.find_all('div', class_='g')
#             if not search_results:
#                 search_results = soup.find_all('div', class_='yuRUbf')
                
#             # Print for debugging
#             log_info(f"Found {len(search_results)} search results for Wiki")
            
#             for result in search_results:
#                 link = result.find('a')
#                 if link and 'href' in link.attrs:
#                     url = link['href']
#                     if 'wikipedia.org' in url or 'fandom.com' in url:
#                         urls['wiki_url'] = url
#                         break
        
#         # # If we still don't have URLs, try direct known patterns
#         # if 'official_url' not in urls and 'zelda' in game_title.lower():
#         #     game_slug = game_title.lower().replace('the legend of zelda: ', '').replace(' ', '-')
#         #     urls['official_url'] = f"https://www.nintendo.com/games/detail/the-legend-of-zelda-{game_slug}-switch/"
            
#         # if 'wiki_url' not in urls and 'zelda' in game_title.lower():
#         #     game_slug = game_title.replace('The Legend of Zelda: ', '').replace(' ', '_')
#         #     urls['wiki_url'] = f"https://zelda.fandom.com/wiki/The_Legend_of_Zelda:_{game_slug}"
        
#         # Log results
#         log_info(f"Found URLs for {game_title}: {urls}")
#         if not urls:
#             log_warning(f"No URLs found for {game_title}")
            
#     except Exception as e:
#         log_error(f"Error finding game URLs: {str(e)}")
#         log_error("Stack trace:", exc_info=True)
    
#     return urls

def fetch_game_info(game_code: str) -> Dict[str, str]:
    """
    Fetch information about a game using Wikipedia API.
    """
    if game_code not in GAME_CODES:
        raise ValueError(f"Unknown game code: {game_code}")
    
    game_title = GAME_CODES[game_code]
    game_info = {
        "title": game_title,
        "description": "",
        "features": [],
        "base_tags": []
    }
    
    try:
        import wikipedia
        
        # Search for the game
        search_results = wikipedia.search(game_title)
        if not search_results:
            search_results = wikipedia.search(f"{game_title} video game")
            
        if search_results:
            try:
                # Get the page for the first result
                page = wikipedia.page(search_results[0], auto_suggest=False)
                
                # Get summary and content
                game_info["description"] = wikipedia.summary(search_results[0], sentences=10)
                
                # Extract key words for tags from content
                content = page.content.lower()
                # Common gaming-related words to look for
                gaming_terms = [
                    "action", "adventure", "rpg", "puzzle", "combat", "exploration",
                    "quest", "dungeon", "boss", "multiplayer", "story", "open-world",
                    "fantasy", "missions", "characters", "abilities", "weapons",
                    "magic", "skills", "levels", "achievements"
                ]
                
                # Extract potential tags from content
                found_terms = [term for term in gaming_terms if term in content]
                
                # # Add game-specific terms
                # if "zelda" in game_title.lower():
                #     found_terms.extend(["zelda", "nintendo", "adventure", "action"])
                # elif "pokemon" in game_title.lower():
                #     found_terms.extend(["pokemon", "nintendo", "rpg", "gaming"])
                
                # Clean and deduplicate tags
                game_info["base_tags"] = list(set([
                    term.replace(" ", "").lower() 
                    for term in found_terms 
                    if len(term) > 3
                ]))
                
                
                log_info(f"Successfully fetched Wikipedia info for {game_title}")
                print(game_info)
                
            except wikipedia.exceptions.DisambiguationError as e:
                # If we get a disambiguation page, try to find the video game entry
                for option in e.options:
                    if "video game" in option.lower():
                        try:
                            page = wikipedia.page(option, auto_suggest=False)
                            game_info["description"] = wikipedia.summary(option, sentences=3)
                            break
                        except:
                            continue
                            
            except wikipedia.exceptions.PageError:
                log_warning(f"No Wikipedia page found for {game_title}")
                
    except Exception as e:
        log_error(f"Error fetching game info: {str(e)}")
        log_error("Stack trace:", exc_info=True)
    
    # # If we didn't get a description, use a fallback
    # if not game_info["description"]:
    #     if "zelda" in game_title.lower():
    #         game_info["description"] = (
    #             f"{game_title} is an action-adventure game in The Legend of Zelda series "
    #             "developed and published by Nintendo. Players explore a vast world, solve puzzles "
    #             "in dungeons, and uncover an epic story in the land of Hyrule."
    #         )
    #     elif "pokemon" in game_title.lower():
    #         game_info["description"] = (
    #             f"{game_title} is a role-playing video game in the Pokémon series. "
    #             "Players embark on a journey to become a Pokémon master, catching and "
    #             "training creatures while exploring a vibrant world."
    #         )
    
    return game_info

def clean_transcript(transcript: str) -> str:
    """Clean up transcript text for better processing."""
    # Remove timestamp patterns
    cleaned = re.sub(r'\[\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}\.\d{3}\]', '', transcript)
    # Remove extra whitespace
    cleaned = ' '.join(cleaned.split())
    return cleaned

def summarize_long_transcript(transcript: str, model: OllamaLLM, max_length: int = 4000) -> str:
    """
    Summarize long transcript by identifying and extracting the most interesting parts.
    Returns original transcript if it's under max_length.
    """
    if len(transcript) <= max_length:
        return transcript
        
    log_info(f"Transcript length ({len(transcript)} chars) exceeds {max_length}, generating summary...")
    
    summary_prompt = ChatPromptTemplate.from_template("""
You are analyzing a video game gameplay transcript. Identify and extract the MOST INTERESTING and IMPORTANT parts of this transcript to create a shorter version that captures the key moments and events.

Focus on:
- Major achievements or discoveries
- Interesting gameplay moments
- Significant progress or obstacles overcome
- Unique or funny interactions
- Key story developments
- Notable reactions or commentary

Create a condensed version that includes these important moments while maintaining their original context and dialogue. Keep the most engaging and entertaining parts.

TRANSCRIPT:
{text}

Provide ONLY the condensed transcript with the best parts, maintaining the original dialogue and descriptions. Do not summarize - keep the actual dialogue and commentary from these important moments.
""")
    
    try:
        condensed = model.invoke(summary_prompt.format(text=transcript))
        log_info(f"Generated condensed transcript: {len(condensed)} chars")
        return condensed
    except Exception as e:
        log_error(f"Error summarizing transcript: {e}")
        # Return a truncated version of original as fallback
        return transcript[:max_length]

def clean_json_output(output: str) -> str:
    """Clean model output to ensure valid JSON."""
    try:
        # Log the raw output for debugging
        log_info(f"Raw model output before cleaning: {output}")
        
        # Remove comments (anything after //)
        lines = []
        for line in output.split('\n'):
            if '//' in line:
                line = line.split('//')[0]
            lines.append(line)
        output = '\n'.join(lines)
        
        # Remove any extra whitespace/newlines
        output = re.sub(r'\s+', ' ', output)
        
        # Extract just the JSON object (everything between first { and last })
        match = re.search(r'\{.*\}', output)
        if match:
            output = match.group(0)
        else:
            raise ValueError("No JSON object found in output")
        
        # Clean up common formatting issues
        output = output.replace('\n', '')
        output = output.replace('  ', ' ')
        output = re.sub(r',\s*}', '}', output)  # Remove trailing commas
        output = re.sub(r'\["([^"]+)"\]', '["\\1"]', output)  # Fix array formatting
        
        # Fix common quote issues
        output = output.replace('" ', '"')
        output = output.replace(' "', '"')
        output = output.replace('\\"', '"')
        
        # Validate JSON before returning
        try:
            json.loads(output)
        except json.JSONDecodeError as e:
            log_error(f"Invalid JSON after cleaning: {output}")
            log_error(f"JSON validation error: {str(e)}")
            raise
            
        log_info(f"Cleaned JSON output: {output}")
        return output
    except Exception as e:
        log_error(f"Error in clean_json_output: {str(e)}")
        log_error(f"Original output: {output}")
        raise
    
def generate_tags(content_info: dict, game_info: dict) -> List[str]:
    """
    Generate comprehensive tag list combining game-specific and content-specific tags.
    """
    # Start with content-specific tags
    tags = content_info.get("hashtags", "").replace("#", "").split()
    
    # Add base tags from game info
    tags.extend(game_info.get("base_tags", []))
    
    # Clean and deduplicate tags
    clean_tags = []
    for tag in tags:
        # Remove special characters and spaces
        clean_tag = re.sub(r'[^\w\s]', '', tag.lower())
        clean_tag = clean_tag.replace(' ', '')
        if clean_tag and len(clean_tag) > 2:  # Only keep tags with 3+ characters
            clean_tags.append(clean_tag)
    
    # Return unique tags, limited to 20
    return list(set(clean_tags))[:20]

def generate_metadata(transcript: str, channel_type: str, game_code: str, context_length: int = 12196) -> dict:
    """
    Generate metadata for a video based on its transcript, channel type, and game information.
    """
    if channel_type not in CHANNEL_TEMPLATES:
        raise ValueError(f"Invalid channel type: {channel_type}")
        
    if game_code not in GAME_CODES:
        raise ValueError(f"Invalid game code: {game_code}")

    try:
        start_time = datetime.now()
        log_info(f"Starting metadata generation for channel type: {channel_type}, game: {game_code}")
        
        # Fetch game information
        game_info = fetch_game_info(game_code)
        
        # Clean and process transcript
        cleaned_transcript = clean_transcript(transcript)
        
        # Initialize model
        model = setup_ollama_model(context_length)
        
        # Summarize if needed
        processed_transcript = summarize_long_transcript(cleaned_transcript, model)
        
        # Prepare enhanced prompt with game context
        metadata_prompt = ChatPromptTemplate.from_template("""
Based on this transcript and game information, generate engaging YouTube video metadata.
The video is about the game: {game_title}

Game Information:
{game_description}

Generate these elements using the transcript for episode-specific content and game information for context:

1. Title:
   IMPORTANT: The title must accurately reflect events that happen in this specific video!
   Choose a style that fits what actually occurs:
   - For exploration: "Discovering the Secrets of [Area]! 🗺️"
   - For challenges: "Solving the Trickiest Puzzle Yet! 🧩"
   - For progression: "Finally Unlocking the [Actual Feature]! ✨"
   - For discoveries: "Found Something Amazing in [Real Location]! 👀"
   DO NOT overhype or mislead about content
   NO "gone wrong", "you won't believe", or similar clickbait
   Use 1-2 relevant emojis maximum

2. Attention-Grabbing Summary:
   - Focus on the specific events/achievements in this episode
   - Reference game-specific elements
   - Start with 1-2 relevant emojis
   Example: "🗺️ Join the exploration of a mysterious ancient ruin filled with clever puzzles!"

3. Content Paragraph:
   - Combine episode-specific events with game context
   - Reference game mechanics and features
   - Use game-specific terminology
   - Add occasional emojis for emphasis
   Example: "Today we explore the eastern wing of the ruins, discovering ancient mechanisms and solving water-based puzzles. Each room brings new challenges as we try to understand the purpose of these mysterious contraptions. 🏰"

4. Subscribe Catch Phrase:
   - Reference the game series/genre
   - Keep it friendly and natural
   Example: "Join our community for more discoveries! SUBSCRIBE and LIKE! ⭐"

5. Final Hook Line:
   - Reference specific game mechanics or story elements
   - Create natural curiosity about what's next
   Example: "What secrets lie behind the next door? See you in the next episode! 🗝️"

6. Three Relevant Hashtags:
   - Based on actual video content
   - Include game-specific terms
   Example: "#exploration #puzzles #adventure"

7. Comment Call-to-Action:
   - Ask about specific moments
   - Reference game mechanics or features
   Example: "What's your approach to solving water puzzles? Share your strategies below! 💭"

Transcript:
{text}

(Do not put it as a text block, do not put ```json``` and please add no comments. make sure to spell the following words correctly, also no written new line characters)
Respond with ONLY a JSON object in this exact format:
{{"title": "Example Title","attention_summary": "Example Summary","content_paragraph": "Example Content","subscribe_catch": "Example Catch","final_catch": "Example Hook","hashtags": "#tag1 #tag2 #tag3","comment_call": "Example Call"}}
""")

        # Generate metadata with game context
        result = model.invoke(metadata_prompt.format(
            game_title=game_info["title"],
            game_description=game_info["description"],
            text=processed_transcript
        ))
        
        # Clean and parse JSON
        cleaned_json = clean_json_output(result)
        try:
            metadata = json.loads(cleaned_json)
            # Validate required fields
            required_fields = ["title", "attention_summary", "content_paragraph", 
                             "subscribe_catch", "final_catch", "hashtags", "comment_call"]
            missing_fields = [field for field in required_fields if field not in metadata]
            if missing_fields:
                raise ValueError(f"Missing required fields in metadata: {missing_fields}")
                
        except json.JSONDecodeError as e:
            log_error(f"Error parsing cleaned JSON: {e}")
            log_error(f"Cleaned JSON: {cleaned_json}")
            raise
        
        # Generate enhanced tags
        enhanced_tags = generate_tags(metadata, game_info)
        
        # Apply channel template
        template = CHANNEL_TEMPLATES[channel_type]
        current_date = datetime.now().strftime("%b %d, %Y")
        
        title = template['title_format'].format(
            title=metadata['title'],
            date=current_date
        )
        
        description = template['description_format'].format(
            attention_summary=metadata['attention_summary'],
            content_paragraph=metadata['content_paragraph'],
            subscribe_catch=metadata['subscribe_catch'],
            final_catch=metadata['final_catch'],
            hashtags=" ".join([f"#{tag}" for tag in enhanced_tags]),
            comment_call=metadata['comment_call']
        )
        
        final_result = {
            "title": title,
            "description": description,
            "tags": enhanced_tags
        }
        
        generation_time = datetime.now() - start_time
        log_info(f"Metadata generation completed in {generation_time.total_seconds():.2f} seconds")
        
        # Log results for verification
        log_info("Generated Title: " + title)
        log_info("First 100 chars of description: " + description[:100])
        
        return final_result
        
    except Exception as e:
        log_error(f"Error generating metadata: {e}")
        log_error(f"Stack trace: ", exc_info=True)
        raise

if __name__ == "__main__":
    # Example usage
    with open('sample_transcript.txt', 'r', encoding='utf-8') as f:
        sample_transcript = f.read()
        
    try:
        metadata = generate_metadata(sample_transcript, "VGL", "ZEOW")
        print("\nGenerated Metadata:")
        print(json.dumps(metadata, indent=2))
    except Exception as e:
        print(f"Error generating metadata: {e}")