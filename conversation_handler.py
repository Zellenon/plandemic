import random
from dialogue import generate_dialogue

def try_conversation(agent1, agent2, current_turn):
    """Attempt a conversation between two agents."""
    conversation_chance = 0.99  # 50% chance
    cooldown_turns = 3        # Minimum turns between conversations

    if (random.random() < conversation_chance and
        current_turn - agent1.last_conversation_turn >= cooldown_turns and
        current_turn - agent2.last_conversation_turn >= cooldown_turns):

        # Generate dialogue for both agents
        dialogue1 = generate_dialogue(agent1, agent2)
        dialogue2 = generate_dialogue(agent2, agent1)

        # Store conversation in memory
        agent1.remember_conversation(agent2.id, dialogue1)
        agent2.remember_conversation(agent1.id, dialogue2)

        # Update cooldown
        agent1.last_conversation_turn = current_turn
        agent2.last_conversation_turn = current_turn

        # Print the conversation for debugging
        print(f"Agent {agent1.id} to Agent {agent2.id}: {dialogue1}")
        print(f"Agent {agent2.id} to Agent {agent1.id}: {dialogue2}")

def handle_room_conversations(agents, current_turn):
    """Trigger conversations between agents in the same room."""
    room_groups = {}

    # Group agents by room
    for agent in agents:
        if agent.current_room not in room_groups:
            room_groups[agent.current_room] = []
        room_groups[agent.current_room].append(agent)

    # Attempt conversations for each group
    for room, agents_in_room in room_groups.items():
        if len(agents_in_room) > 1:
            for i in range(len(agents_in_room)):
                for j in range(i + 1, len(agents_in_room)):
                    try_conversation(agents_in_room[i], agents_in_room[j], current_turn)
