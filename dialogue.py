from text_api import text_controller
from typing import List
from roles import Role


async def generate_dialogue(agent1, agent2):
    """Generate dialogue between two agents using OpenAI API."""
    if agent1.role == Role.IMPOSTOR:
        # Generate dialogue for the impostor
        system_prompt = f"""
        You are an impostor witch in a simulation. Your goal is to deceive the other witches.
        Engage in a conversation by asking questions to the other witch and responding to their inquiries.
        Try to deflect suspicion and create doubt about the other witches.
        """
    else:
        # Generate dialogue for a regular witch
        system_prompt = f"""
        You are a witch in a simulation. Your goal is to collect ingredients and identify the impostor.
        Engage in a conversation by asking questions to the other witch and responding to their inquiries.
        Share your observations and suspicions about the impostor.
        """

    user_message = f"Generate a response based on your current situation, including questions to ask the other agent. Your name is {agent1.name}."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    # Call the updated `client.chat.completions.create` method
    response = await text_controller.generate(messages)

    # Include the agent's ID in the response for clarity
    return f"{agent1.name}: {response}"


async def assess_suspicion(dialogues: List[str]) -> List[int]:
    """Assess the suspicion levels of multiple dialogues using OpenAI API."""
    system_prompt = "You are an evaluator of dialogues in a simulation. Your task is to assess the level of suspicion in the following dialogues:\n\n"

    # Create a formatted string for all dialogues
    for i, dialogue in enumerate(dialogues):
        system_prompt += f'Dialogue {i + 1}: "{dialogue}"\n'

    system_prompt += "Please rate the suspicion level for each dialogue on a scale from 1 to 10, where 1 is not suspicious at all and 10 is extremely suspicious. Provide a brief explanation for your rating for each dialogue."

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    # Call the OpenAI API to assess suspicion
    response = await text_controller.generate(messages)

    # Debugging: Print the response to check its structure
    # Add this line to inspect the response
    print("Response from API:", response)

    # Parse the response to extract suspicion levels
    suspicion_scores = []
    dialogues = response.split("\n\n")  # Split the response into dialogues

    for dialogue in dialogues:
        lines = dialogue.split("\n")
        if len(lines) >= 2 and "Suspicion Level:" in lines[1]:
            try:
                score = int(lines[1].split(": ")[1])  # Extract the score
                suspicion_scores.append(score)
            except (IndexError, ValueError):
                raise ValueError("Unexpected response format: {}".format(response))

    return suspicion_scores
