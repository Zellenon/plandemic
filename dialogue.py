import openai
import os

# Set your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_dialogue(agent1, agent2):
    """Generate dialogue between two agents using OpenAI API."""
    system_prompt = f"""
    You are an NPC in a simulation. Your personality is {agent1.personality}.
    You are currently talking to another NPC with the personality {agent2.personality}.
    Respond as if you are roleplaying with your personality.
    """
    user_message = f"You are interacting with {agent2.personality}. Generate a response based on your personality."

    response = openai.Chat.create(
        model="gpt-4",  # Use "gpt-4" or "gpt-3.5-turbo" based on your API access
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        max_tokens=100,
        temperature=0.7,
    )

    return response['choices'][0]['message']['content']
