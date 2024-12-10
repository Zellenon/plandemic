import random
from dialogue import generate_dialogue
import math

def try_conversation(agent1, agent2, current_turn, distance_threshold=5.0):
    """Attempt a conversation between two agents if they are close."""
    if not agent1.is_close(agent2, distance_threshold):
        return

    # Dynamic conversation chance based on sociability or personality
    sociability_map = {"friendly": 0.7, "neutral": 0.5, "hostile": 0.3}
    conversation_chance = (sociability_map[agent1.personality] + sociability_map[agent2.personality]) / 2
    cooldown_turns = 3  # Minimum turns between conversations

    if (random.random() < conversation_chance and
        current_turn - agent1.last_conversation_turn >= cooldown_turns and
        current_turn - agent2.last_conversation_turn >= cooldown_turns):

        # Generate dialogue for both agents
        dialogue1 = f"Hello from {agent1.id} to {agent2.id}!"
        dialogue2 = f"Hi back from {agent2.id} to {agent1.id}!"

        # Store conversation in memory
        agent1.remember_conversation(agent2.id, dialogue1)
        agent2.remember_conversation(agent1.id, dialogue2)

        # Update cooldown
        agent1.last_conversation_turn = current_turn
        agent2.last_conversation_turn = current_turn

        # Print the conversation for debugging
        print(f"Agent {agent1.id} to Agent {agent2.id}: {dialogue1}")
        print(f"Agent {agent2.id} to Agent {agent1.id}: {dialogue2}")

def handle_room_conversations(agents, current_turn, distance_threshold=5.0):
    """Trigger conversations between agents in the same room, considering proximity."""
    room_groups = {}

    # Group agents by room
    for agent in agents:
        room_groups.setdefault(agent.current_room, []).append(agent)

    # Attempt conversations for each group
    for room, agents_in_room in room_groups.items():
        if len(agents_in_room) > 1:
            # Shuffle agents to randomize pairings
            random.shuffle(agents_in_room)
            for i in range(len(agents_in_room)):
                for j in range(i + 1, len(agents_in_room)):
                    try_conversation(
                        agents_in_room[i],
                        agents_in_room[j],
                        current_turn,
                        distance_threshold
                    )


