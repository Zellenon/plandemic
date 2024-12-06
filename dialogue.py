import openai
import os

# Set your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_dialogue(agent, other_agent):
    """Generate dialogue using GPT-4o mini."""
    prompt = f"""
    You are an NPC in a simulation. Your personality is {agent.personality}. 
    You are talking to Agent {other_agent.id}. 
    Respond naturally, given your personality and the context of the game.
    """
    response = openai.Completion.create(
        engine="gpt-4o-mini",
        prompt=prompt,
        max_tokens=50,
        temperature=0.7
    )
    return response['choices'][0]['text'].strip()
