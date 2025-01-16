import openai
import speech_recognition as sr
import pyttsx3
import time
import pygame
import sys

# Replace with your OpenAI API key
apiKey = 'replace-ur-key'
client = openai.OpenAI(api_key=apiKey)

# Dictionary to store the state of each appliance (True = On, False = Off)
appliance_states = {
    "light": False,
    "fan": False,
    "ac": False,
    "heater": False,
}

# Initialize the text-to-speech engine
engine = pyttsx3.init()

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AiSHA Home Simulator")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 255, 0)

# Room positions and sizes
ROOMS = {
    "Living Room": pygame.Rect(50, 50, 300, 250),
    "Bedroom": pygame.Rect(350, 50, 300, 250),
    "Kitchen": pygame.Rect(50, 299, 250, 200),
    "Washroom": pygame.Rect(300, 299, 250, 200)
}

# Circle positions in each room (x, y)
CIRCLE_POSITIONS = {
    "Living Room": [(100, 100)],  # fan
    "Bedroom": [(400, 100)],      # ac
    "Kitchen": [(100, 350)],      # light
    "Washroom": [(350, 350)]      # heater
}

# Initialize the state of each circle to False
circle_states = {
    "Living Room": [False],  # fan
    "Bedroom": [False],      # ac
    "Kitchen": [False],      # light
    "Washroom": [False]      # heater
}

# Font for room labels
font = pygame.font.Font(None, 36)

# Load and scale the AI system images
ai_image_active = pygame.image.load("aishaLogoRed.png")  # Replace with actual file name
ai_image_idle = pygame.image.load("aishaLogoWhite.png")
ai_image_idle = pygame.transform.scale(ai_image_idle, (100, 100))
ai_image_active = pygame.transform.scale(ai_image_active, (100, 100))

ai_image = ai_image_idle

# Position the image at the bottom right corner with a 10px padding
ai_image_rect = ai_image.get_rect()
ai_image_rect.bottomright = (WIDTH - 10, HEIGHT - 10)  # 10px padding from the edges

# Function to draw the AI system
def draw_ai_system(ai_active):
    # Set the AI image based on the active state
    if ai_active:
        screen.blit(ai_image_active, ai_image_rect)
    else:
        screen.blit(ai_image_idle, ai_image_rect)

# Function to draw rooms and circles
def draw_rooms_and_circles():
    for room_name, room_rect in ROOMS.items():
        # Draw the room
        pygame.draw.rect(screen, GRAY, room_rect)
        pygame.draw.rect(screen, BLACK, room_rect, 3)  # Room border
        # Room label
        label = font.render(room_name, True, BLACK)
        label_rect = label.get_rect(center=room_rect.center)
        screen.blit(label, label_rect)
        
        # Draw circles in the room
        for idx, pos in enumerate(CIRCLE_POSITIONS[room_name]):
            color = GREEN if circle_states[room_name][idx] else WHITE
            pygame.draw.circle(screen, color, pos, 20)
            pygame.draw.circle(screen, BLACK, pos, 20, 2)  # Circle border
            

# Function to update the circle states based on appliance commands
def update_circle_states():
    circle_states["Living Room"][0] = appliance_states["fan"]     # fan state
    circle_states["Bedroom"][0] = appliance_states["ac"]          # ac state
    circle_states["Kitchen"][0] = appliance_states["light"]       # light state
    circle_states["Washroom"][0] = appliance_states["heater"]     # heater state

# Function to speak text using pyttsx3
def speak_text(text):
    engine.say(text)
    engine.runAndWait()

# Function to capture voice input and convert to text
def get_voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)

    try:
        user_input = recognizer.recognize_google(audio)
        print(f"You said: {user_input}")
        return user_input.lower()
    except sr.UnknownValueError:
        print("Sorry, I did not understand the audio.")
        return None
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        return None

# Use OpenAI's GPT-3.5-turbo to get a response
def get_ai_response(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Improved keyword-based approach for appliance commands
def control_device(prompt):
    global ai_image
    ai_image = ai_image_active  # AI is actively processing

    for appliance in appliance_states.keys():
        if appliance in prompt.lower():
            if "on" in prompt.lower():
                appliance_states[appliance] = True
                update_circle_states()
                return f"The {appliance} has been turned on."
            elif "off" in prompt.lower():
                appliance_states[appliance] = False
                update_circle_states()
                return f"The {appliance} has been turned off."
    return None

# Determine if input is command or question
def determine_intent(user_input):
    intent_check = f"Is the following input an appliance command or a question? '{user_input}' Answer in one word only, command or question."
    intent = get_ai_response(intent_check)
    print("intent: ", intent)
    
    if "command" in intent.lower():
        return "command"
    else:
        return "question"

# Function to get the chatbot's response
def chatbot_response(user_input):
    global ai_image
    ai_image = ai_image_active  # AI is actively processing

    intent = determine_intent(user_input)

    if intent == "command":
        action_response = control_device(user_input)
        if action_response:
            return action_response

        ai_response = get_ai_response(user_input)
        action_response = control_device(ai_response)
        if action_response:
            return action_response
        else:
            return "I didn't understand the command."
    
    elif intent == "question":
        question_prompt = f"{user_input}, give a straightforward, direct and concise answer, not more than 80 words. Your name is AiSHA, an AI-enabled smart home automation system."
        ai_response = get_ai_response(question_prompt)
        return ai_response if len(ai_response.split()) <= 80 else ai_response[:80] + "..."

# Wait for activation
def wait_for_activation():
    activation_keywords = ["aisha", "ayesha", "isha", "asha"]
    
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Idle Mode. Say 'Aisha' to activate or 'exit' to quit.")
        audio = recognizer.listen(source)

    try:
        user_input = recognizer.recognize_google(audio)
        
        if "exit" in user_input.lower():
            return "exit"
        
        if any(keyword in user_input.lower() for keyword in activation_keywords):
            print("ActiveListen Mode Activated.")
            speak_text("Yes, I'm listening!")
            return True
    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
    
    return False

# Main loop for voice interaction and pygame
if __name__ == "__main__":
    print("Welcome to AiSHA. Say 'Aisha' to activate the system.")
    speak_text("Welcome to AiSHA. Say Aisha to activate the system.")

    running = True
    ai_active = True
    while running:
        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

        # Update the circle states in case appliance status has changed
        update_circle_states()

        # Clear screen
        screen.fill(WHITE)

        # Draw rooms, circles, and AI system
        draw_rooms_and_circles()
        draw_ai_system(ai_active)

        # Pygame display update
        pygame.display.flip()

        # Wait for user to activate
        activation = wait_for_activation()
        if activation == "exit":
            print("Exiting the program.")
            speak_text("Exiting the program.")
            running = False
            break

        elif activation:
            ai_active = True  # AI is now active
            draw_ai_system(ai_active)
            user_input = get_voice_input()
            if user_input is None:
                continue
            if user_input.lower() == "exit":
                print("Exiting the program.")
                speak_text("Exiting the program.")
                running = False
                break
            elif user_input:
                response = chatbot_response(user_input)
                print(f"AI response: {response}")
                speak_text(response)
            ai_active = False
            draw_ai_system(ai_active)  # Return AI to idle mode