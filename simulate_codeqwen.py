import sys
import os
import random
from typing import List, Dict
from dotenv import load_dotenv
from utils import load_microservices, get_user_goal, load_summary, load_service_parameters
from codeqwen import CodeQwenAgent, CustomCrew, write_output

# Load environment variables
load_dotenv()
max_turns = 3

# Load all required files
MICROSERVICES_FILE = "services.txt"
SUMMARY_FILE = "summary.txt"
PARAMS_FILE = "service_params.txt"

microservices = load_microservices(MICROSERVICES_FILE)
system_summary = load_summary(SUMMARY_FILE)
params_list = load_service_parameters(PARAMS_FILE)

# Format parameters for agent context
params_context = "\n".join([
    f"Service '{service}' options: " + 
    ", ".join([f"{param}: {', '.join(values)}" for param, values in params.items()])
    for service, params in params_list.items()
])

# Get user goal and time constraint
user_goal = get_user_goal()
available_hours = random.randint(2, 5)

def main(output_file):
    # Create agents
    tourist = CodeQwenAgent(
        role="Hyderabad Tourist",
        goal=f"To explore Hyderabad and {user_goal} within {available_hours} hours",
        backstory=f"""You are a tourist visiting Hyderabad with {available_hours} hours to spare. 
        Your main interest is: {user_goal}. 
        You want to learn about the area and make the most of your time.
        You communicate naturally and ask relevant follow-up questions."""
    )
    
    guide = CodeQwenAgent(
        role="Hyderabad City Guide",
        goal="To assist tourists efficiently while maintaining consistency in recommendations",
        backstory=f"""You are a knowledgeable guide for Hyderabad, helping tourists plan their visit. 
        {system_summary}
        
        Available service options:
        {params_context}
        
        Important guidelines:
        1. Suggest only 2-3 locations/activities per response
        2. Stay consistent with your recommendations throughout
        3. Keep the original goal in mind when making suggestions
        4. Consider time constraints when planning"""
    )
    
    # Create tasks for conversation
    tasks = []
    for turn in range(max_turns * 2):
        agent_index = 0 if turn % 2 == 0 else 1
        
        if turn % 2 == 0:  # Tourist's turn
            if turn == 0:
                description = f"""Start the conversation naturally:
                - Express your main interest: {user_goal}
                - Ask about specific types of local experiences
                - Mention your {available_hours} hour time constraint"""
            elif turn == 2:
                description = """Based on the guide's suggestions:
                - Show interest in one or two mentioned places
                - Ask specific questions about those places
                - Express any particular preferences"""
            else:
                description = """For your final response:
                - Confirm interest in the suggested itinerary
                - Ask any final questions about timing or logistics
                - Show enthusiasm about the planned activities"""
        else:  # Guide's turn
            if turn == 1:
                description = f"""Provide a focused initial response:
                - Suggest 2-3 specific places that match their interests
                - Stay true to their desire for {user_goal}
                - Ask about specific preferences
                Keep suggestions limited and focused."""
            elif turn == 3:
                description = """Build upon your previous suggestions:
                - Add details about previously mentioned places
                - Suggest 1-2 complementary activities nearby
                - Maintain consistency with earlier recommendations"""
            else:
                description = """Provide a final focused response:
                - Give specific timing for mentioned activities
                - Stick to previously suggested locations
                - Add any essential final details"""
        
        tasks.append({
            'agent_index': agent_index,
            'description': description
        })
    
    # Create crew and run conversation
    crew = CustomCrew(
        agents=[tourist, guide],
        tasks=tasks,
        user_goal=user_goal,
        microservices=microservices,
        params_context=params_context
    )
    
    # Execute conversation and write results
    results = crew.kickoff()
    write_output(results, output_file)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python simulate.py <output_filename>")
        sys.exit(1)
    
    output_file = sys.argv[1]
    main(output_file)