import os
import json
import re
from typing import Dict, List, Optional, Tuple

def get_goal_mapping() -> Dict[str, Tuple[str, List[str]]]:
    """Return mapping of goals to their category and expected services"""
    return {
        "The Golconda Fort sounds fascinating! I'd like to explore it thoroughly. What's the best way to get there?": 
            ("concrete", ["historical_info", "crowd_monitor", "ticket_purchase"]),
        "I'd love to visit Charminar and understand its history. Wonder if it gets too crowded on weekends?":
            ("concrete", ["historical_info", "crowd_monitor"]),
        "I'm really interested in visiting Salar Jung Museum. Do they have any special exhibitions going on?":
            ("concrete", ["historical_info", "exhibition_tracker"]),
        "The Qutub Shahi Tombs look beautiful in photos. How can I plan a visit there?":
            ("concrete", ["historical_info", "crowd_monitor"]),
        "I'm thinking of spending some time near Hussain Sagar Lake. How clean is the water there?":
            ("concrete", ["water_quality", "air_quality"]),
        "Would love to enjoy the sunset at Tank Bund. Is it usually very crowded in the evenings?":
            ("concrete", ["water_quality", "crowd_monitor"]),
        "Would love to visit Durgam Cheruvu for a peaceful evening. Is the area nice for walking?":
            ("concrete", ["water_quality", "air_quality"]),
        "I want to explore Laad Bazaar for traditional bangles. What's the best way to reach there?":
            ("concrete", ["crowd_monitor", "travel_options"]),
        "Planning to visit GVK One for some shopping. Is it usually very crowded on weekdays?":
            ("concrete", ["crowd_monitor", "travel_options"]),
        "Craving some authentic Hyderabadi biryani! Any vegetarian-friendly places you'd recommend?":
            ("concrete", ["restaurant_finder"]),
        "Would love to try some street food. Any areas famous for chaat and local snacks?":
            ("concrete", ["restaurant_finder", "crowd_monitor"]),
        "Are there any cultural exhibitions happening in the city? Particularly interested in traditional art.":
            ("concrete", ["exhibition_tracker", "ticket_purchase"]),
        "Would love to see some local handicraft exhibitions. Anything interesting coming up?":
            ("concrete", ["exhibition_tracker", "ticket_purchase"]),
        "Thinking of visiting Snow World. Is it usually very crowded?":
            ("concrete", ["ticket_purchase", "crowd_monitor"]),
        "Planning to visit Ramoji Film City. What's the best way to plan this trip?":
            ("concrete", ["ticket_purchase", "travel_options"]),
        "Looking for a good place serving traditional Irani chai and Osmania biscuits!":
            ("concrete", ["restaurant_finder"]),
        "Any photography exhibitions or galleries worth visiting this week?":
            ("concrete", ["exhibition_tracker"]),
        "I've heard Gandipet Lake is beautiful. How's the water quality there these days?":
            ("concrete", ["water_quality", "air_quality"]),
        "My grandparents always talk about Hyderabad's old charm. Want to experience that authentic vibe and maybe try some traditional snacks.":
            ("ambiguous", ["historical_info", "crowd_monitor", "restaurant_finder"]),
        "Been reading about Hyderabad's royal history. Would love to see some of that grandeur and taste what the Nizams enjoyed!":
            ("ambiguous", ["historical_info", "restaurant_finder", "crowd_monitor"]),
        "I keep seeing these gorgeous lake photos on Instagram. Would love to spend an evening there and grab dinner nearby!":
            ("ambiguous", ["water_quality", "crowd_monitor", "restaurant_finder"]),
        "Love those bustling market vibes, you know? Where locals shop and grab quick bites. That's my scene!":
            ("ambiguous", ["crowd_monitor", "restaurant_finder", "travel_options"]),
        "Love anything artsy with a story behind it. Places where I can learn about local culture while enjoying the atmosphere.":
            ("ambiguous", ["exhibition_tracker", "historical_info", "restaurant_finder"]),
        "History nerd but also a foodie. Want to explore places that tell a story while munching on local specialties!":
            ("ambiguous", ["historical_info", "restaurant_finder", "exhibition_tracker"]),
        "First time in Hyderabad! Want to start with the locals' favorites, not the tourist checklist.":
            ("ambiguous", ["restaurant_finder", "crowd_monitor", "travel_options"])
    }

def parse_single_file(file_path: str) -> Dict:
    """Parse a single conversation file and extract required components"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Initialize result structure
    result = {
        "conversation": [],
        "service_tracking": [],
        "original_goal": "",
        "goal_category": "",
        "expected_services": [],
        "core_services": "",
        "final_summary": "",
        "usage_metrics": {}
    }

    # Extract usage metrics if present
    usage_match = re.search(r"Usage Metrics:\n(.*?)\n\nConversation", content, re.DOTALL)
    if usage_match:
        metrics_text = usage_match.group(1)
        result["usage_metrics"] = {
            k.strip(): int(v.strip()) 
            for k, v in [item.split('=') for item in metrics_text.split() if '=' in item]
        }

    # Extract conversation and service tracking
    conv_section = re.search(r"Conversation with Service Tracking:\n(.*?)\nFinal Plan Summary:", 
                           content, re.DOTALL)
    if conv_section:
        conv_text = conv_section.group(1).strip()
        messages = []
        current_message = []
        current_role = None
        
        for line in conv_text.split('\n'):
            if line.strip() == "Tourist:" or line.strip() == "Guide:":
                if current_role and current_message:
                    messages.append({
                        "role": current_role,
                        "content": "\n".join(current_message).strip()
                    })
                current_role = line.strip()[:-1]  # Remove the colon
                current_message = []
            elif line.startswith("Identified Services after Turn"):
                if current_role and current_message:
                    messages.append({
                        "role": current_role,
                        "content": "\n".join(current_message).strip()
                    })
                    current_message = []
                result["service_tracking"].append(line.strip())
            else:
                current_message.append(line)
        
        if current_role and current_message:
            messages.append({
                "role": current_role,
                "content": "\n".join(current_message).strip()
            })
        
        result["conversation"] = messages

    # Extract original goal and map to category/services
    goal_match = re.search(r"Original Goal: (.*?)\n", content)
    if goal_match:
        goal = goal_match.group(1).strip()
        result["original_goal"] = goal
        goal_map = get_goal_mapping()
        if goal in goal_map:
            category, services = goal_map[goal]
            result["goal_category"] = category
            result["expected_services"] = services

    # Extract core services and parameters
    services_section = re.search(r"Core Services and Parameters:\n(.*?)$", 
                               content, re.DOTALL)
    if services_section:
        result["core_services"] = services_section.group(1).strip()

    # Extract final summary
    summary_section = re.search(r"Final Plan Summary:\n(.*?)\nOriginal Goal:", 
                              content, re.DOTALL)
    if summary_section:
        result["final_summary"] = summary_section.group(1).strip()

    return result

def process_directory(dir_path: str, model_name: str) -> None:
    """Process all files in directory and create consolidated JSON"""
    all_conversations = []
    
    # Get all .txt files
    files = [f for f in os.listdir(dir_path) if f.endswith('.txt')]
    
    # Sort files numerically
    files.sort(key=lambda x: int(x.split('.')[0]))
    
    for file_name in files:
        file_path = os.path.join(dir_path, file_name)
        try:
            conversation_data = parse_single_file(file_path)
            conversation_data["id"] = file_name.split('.')[0]  # Add ID from filename
            all_conversations.append(conversation_data)
        except Exception as e:
            print(f"Error processing {file_name}: {str(e)}")
    
    # Write consolidated JSON
    output_file = f"data_{model_name}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "model": model_name,
            "total_conversations": len(all_conversations),
            "conversations": all_conversations
        }, f, indent=2, ensure_ascii=False)

    print(f"Processed {len(all_conversations)} files into {output_file}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python script.py <directory_path> <model_name>")
        sys.exit(1)
    
    dir_path = sys.argv[1]
    model_name = sys.argv[2]
    process_directory(dir_path, model_name)