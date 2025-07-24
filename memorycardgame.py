import tkinter as tk
from tkinter import messagebox, simpledialog
import random
import pygame
from PIL import Image, ImageTk
import requests
import time
import os

# Initialize Pygame for sound
pygame.mixer.init()

# Load and trim sound effects to 2 seconds
def load_sound(file_path, duration=2):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Sound file not found: {file_path}")
    sound = pygame.mixer.Sound(file_path)
    sound.set_volume(0.5)
    return sound

flip_sound = load_sound("flip.wav")
match_sound = load_sound("match.wav")
win_sound = load_sound("win.wav")

# Flask API URL
API_URL = "http://127.0.0.1:5000/api"

# Initialize the game window
root = tk.Tk()
root.title("Two-Player Memory Game")
root.geometry("800x600")  # Initial window size
root.resizable(True, True)  # Make the window resizable

# Custom fonts and colors
FONT = ("Helvetica", 16)
TITLE_FONT = ("Helvetica", 24, "bold")
BUTTON_FONT = ("Helvetica", 14)
BG_COLOR = "#2E3A40"
TEXT_COLOR = "#DBE0E9"
BUTTON_COLOR = "#5E81AC"
HOVER_COLOR = "#81A1C1"
CARD_BG_COLOR = "#4C566A"

# Game variables
cards = []
flipped = []   # Holds the indices of currently flipped cards
current_player = 1
scores = {1: 0, 2: 0}
turns = {1: 0, 2: 0}
player_names = {1: "", 2: ""}
start_time = 0

# Create a main frame for the game
main_frame = tk.Frame(root, bg=BG_COLOR)
main_frame.pack(fill=tk.BOTH, expand=True)

# Add a title
title_label = tk.Label(main_frame, text="Memory Card Game", font=TITLE_FONT, bg=BG_COLOR, fg=TEXT_COLOR)
title_label.pack(pady=10)

# Create a canvas for the cards
canvas = tk.Canvas(main_frame, bg=BG_COLOR)
canvas.pack(fill=tk.BOTH, expand=True)

# Resize images dynamically based on window size
def resize_image(image_path, width, height):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    image = Image.open(image_path)
    image = image.resize((width, height), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image)

# Load card images (replace with your image paths)
card_images = [
    resize_image("card1.png", 100, 100),
    resize_image("card2.png", 100, 100),
    resize_image("card3.png", 100, 100),
    resize_image("card4.png", 100, 100),
    resize_image("card5.png", 100, 100),
    resize_image("card6.png", 100, 100)
]

# Duplicate card images to create pairs and shuffle them
card_images *= 2
random.shuffle(card_images)

# Create card back image (replace with your card back image)
card_back = resize_image("card_back.png", 100, 100)

# Create cards on the canvas
def create_cards():
    global cards
    cards = []
    
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    card_width = 100
    card_height = 100
    spacing = 10
    rows = 4
    cols = 3

    # Calculate starting positions dynamically for centering the grid
    start_x = (canvas_width - (cols * (card_width + spacing))) // 2
    start_y = (canvas_height - (rows * (card_height + spacing))) // 2

    for i in range(rows):  # For each row
        for j in range(cols):  # For each column
            index = i * cols + j
            x = start_x + j * (card_width + spacing)
            y = start_y + i * (card_height + spacing)
            card_id = canvas.create_image(x, y, anchor="nw", image=card_back)
            card_dict = {
                "id": card_id,
                "image": card_images[index],
                "flipped": False,
                "matched": False
            }
            cards.append(card_dict)
            # Bind click event to each card using a lambda to capture the index
            canvas.tag_bind(card_id, "<Button-1>", lambda e, idx=index: flip_card(idx))

# Flip a card when clicked
def flip_card(index):
    if len(flipped) < 2 and not cards[index]["flipped"] and not cards[index]["matched"]:
        cards[index]["flipped"] = True
        canvas.itemconfig(cards[index]["id"], image=cards[index]["image"])
        flipped.append(index)
        flip_sound.play()  # Play flip sound
        if len(flipped) == 2:
            turns[current_player] += 1
            root.after(1000, check_match)  # Wait 1 second before checking match

# Check if two flipped cards match
def check_match():
    global current_player, start_time
    index1, index2 = flipped
    if cards[index1]["image"] == cards[index2]["image"]:
        cards[index1]["matched"] = True
        cards[index2]["matched"] = True
        scores[current_player] += 1
        match_sound.play()  # Play match sound
        messagebox.showinfo("Match", f"{player_names[current_player]} found a match!")
        if all(card["matched"] for card in cards):
            end_game()
    else:
        # Revert the cards to the card back image
        cards[index1]["flipped"] = False
        cards[index2]["flipped"] = False
        canvas.itemconfig(cards[index1]["id"], image=card_back)
        canvas.itemconfig(cards[index2]["id"], image=card_back)
        messagebox.showinfo("No Match", "Try again!")
        current_player = 3 - current_player  # Switch players
    flipped.clear()
    update_score()

# Update score display on the canvas
def update_score():
    canvas.delete("score")
    canvas_width = canvas.winfo_width()
    score_text = f"{player_names[1]}: {scores[1]} | {player_names[2]}: {scores[2]} | Turns: {turns[1]} vs {turns[2]}"
    canvas.create_text(canvas_width // 2, 20, text=score_text, tags="score", fill=TEXT_COLOR, font=FONT)

# End the game when all matches are found
def end_game():
    global start_time
    winner = 1 if scores[1] > scores[2] else 2 if scores[2] > scores[1] else 0  # 0 for draw
    win_sound.play()  # Play win sound
    game_time = int(time.time() - start_time)
    if winner == 0:
        winner_details = "It's a draw!\n"
    else:
        winner_details = f"Winner: {player_names[winner]}\n"
    winner_details += f"Score: {scores[1]} vs {scores[2]}\nTurns: {turns[1]} vs {turns[2]}\nTime: {game_time}s"
    messagebox.showinfo("Game Over", winner_details)
    save_scores(game_time)
    show_leaderboard()
    restart_game()  # Automatically restart the game

# Save scores to the database via the Flask API
def save_scores(game_time):
    for player_id, score in scores.items():
        try:
            requests.post(f"{API_URL}/save_score", json={"player_id": player_id, "score": score, "time": game_time})
        except Exception as e:
            print("Error saving scores:", e)

# Show leaderboard in a new window
def show_leaderboard():
    try:
        response = requests.get(f"{API_URL}/leaderboard")
        response.raise_for_status()  # Raise error for bad responses
        leaderboard = response.json()
        leaderboard_window = tk.Toplevel(root)
        leaderboard_window.title("Leaderboard")
        leaderboard_window.geometry("300x200")
        leaderboard_window.configure(bg=BG_COLOR)
        tk.Label(leaderboard_window, text="Leaderboard", font=TITLE_FONT, bg=BG_COLOR, fg=TEXT_COLOR).pack(pady=10)
        
        if leaderboard:
            for entry in leaderboard:
                tk.Label(leaderboard_window, text=f"{entry[0]}: {entry[1]} points in {entry[2]} seconds", 
                         font=FONT, bg=BG_COLOR, fg=TEXT_COLOR).pack()
        else:
            tk.Label(leaderboard_window, text="No data available", font=FONT, bg=BG_COLOR, fg=TEXT_COLOR).pack()
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch leaderboard: {e}")

# Restart the game (with proper indentation)
def restart_game():
    global cards, flipped, current_player, scores, turns, start_time, card_images
    # Optionally re-shuffle the cards for a fresh game
    random.shuffle(card_images)
    cards = []
    flipped = []
    current_player = 1
    scores = {1: 0, 2: 0}
    turns = {1: 0, 2: 0}
    start_time = time.time()
    canvas.delete("all")
    create_cards()
    update_score()

# Get player names using input dialogs
def get_player_names():
    player_names[1] = simpledialog.askstring("Player 1", "Enter Player 1's name:", parent=root)
    player_names[2] = simpledialog.askstring("Player 2", "Enter Player 2's name:", parent=root)
    
    if player_names[1] and player_names[2]:
        try:
            response1 = requests.post(f"{API_URL}/register", json={"name": player_names[1]})
            response2 = requests.post(f"{API_URL}/register", json={"name": player_names[2]})
            # You can store player IDs if needed from response1.json() and response2.json()
        except Exception as e:
            print("Error registering players:", e)
    start_game()

# Start the game (initialize game state)
def start_game():
    global start_time
    create_cards()
    start_time = time.time()
    update_score()

# Create a styled button
def create_button(text, command):
    button = tk.Button(main_frame, text=text, font=BUTTON_FONT, bg=BUTTON_COLOR, 
                       fg=TEXT_COLOR, activebackground=HOVER_COLOR, command=command)
    button.pack(pady=10)

# Start by asking for player names
get_player_names()

# Add Restart and Quit buttons
create_button("Restart", restart_game)
create_button("Quit", root.quit)

# Start the main event loop
root.mainloop()
