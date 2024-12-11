from text_api import text_controller


def generate_dialogue(agent1, agent2):
    """Generate dialogue between two agents using OpenAI API."""
    system_prompt = f"""
    You are an NPC in a simulation. Your personality is {agent1.personality}.
    You are currently talking to another NPC with the personality {agent2.personality}.
    Respond as if you are roleplaying with your personality.
    """
    user_message = f"You are interacting with {agent2.personality}. Generate a response based on your personality."

    """Generate dialogue between two agents using OpenAI API."""
    system_prompt = f"""
        You are an NPC in a simulation. Your personality is {agent1.personality}.
        You are currently talking to another NPC with the personality {agent2.personality}.
        Respond as if you are roleplaying with your personality.
        """
    user_message = f"You are interacting with {agent2.personality}. Generate a response based on your personality."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    # Call the updated `client.chat.completions.create` method
    response = text_controller.generate(messages)

    # Access the content from the response
    return response
