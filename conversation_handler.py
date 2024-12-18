import random
from dialogue import generate_dialogue


async def try_conversation(agent1, agent2, current_turn):
    """Attempt a conversation between two agents."""
    conversation_chance = 0.10
    cooldown_turns = 6
    max_distance = 2.0  # Maximum distance for conversation in grid cells

    # First check if they're in the same room
    if agent1.current_room != agent2.current_room:
        return

    # Then check distance between agents
    distance = ((agent1.x - agent2.x) ** 2 + (agent1.y - agent2.y) ** 2) ** 0.5

    if (
        distance <= max_distance
        and random.random() < conversation_chance
        and current_turn - agent1.last_conversation_turn >= cooldown_turns
        and current_turn - agent2.last_conversation_turn >= cooldown_turns
    ):

        # Allow for multiple turns of dialogue
        for _ in range(3):  # Number of exchanges
            # Generate dialogue for agent1
            dialogue1 = await generate_dialogue(agent1, agent2)
            agent1.remember_conversation(agent2.name, dialogue1)

            # Generate dialogue for agent2
            dialogue2 = await generate_dialogue(agent2, agent1)
            agent2.remember_conversation(agent1.name, dialogue2)

            # Print the conversation for debugging
            print(f"{agent1.name} to {agent2.name}: {dialogue1}")
            print(f"{agent2.name} to {agent1.name}: {dialogue2}")

        # Update cooldown
        agent1.last_conversation_turn = current_turn
        agent2.last_conversation_turn = current_turn


async def handle_room_conversations(agents, current_turn):
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
                    # Await the try_conversation function
                    await try_conversation(
                        agents_in_room[i], agents_in_room[j], current_turn
                    )
