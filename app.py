from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('memory_game.db')
    c = conn.cursor()
    # Drop existing tables (if any)
    c.execute("DROP TABLE IF EXISTS players")
    c.execute("DROP TABLE IF EXISTS scores")
    # Create new tables
    c.execute('''CREATE TABLE players
                 (id INTEGER PRIMARY KEY, name TEXT)''')
    c.execute('''CREATE TABLE scores
                 (id INTEGER PRIMARY KEY, player_id INTEGER, score INTEGER, time INTEGER)''')
    conn.commit()
    conn.close()

# Register a new player
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    name = data['name']

    conn = sqlite3.connect('memory_game.db')
    c = conn.cursor()
    c.execute("INSERT INTO players (name) VALUES (?)", (name,))
    player_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'message': 'Player registered successfully', 'player_id': player_id})

# Save score
@app.route('/api/save_score', methods=['POST'])
def save_score():
    data = request.json
    player_id = data['player_id']
    score = data['score']
    time = data['time']

    conn = sqlite3.connect('memory_game.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO scores (player_id, score, time) VALUES (?, ?, ?)", (player_id, score, time))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Score saved successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# Get leaderboard
@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    conn = sqlite3.connect('memory_game.db')
    c = conn.cursor()
    try:
        c.execute("SELECT players.name, scores.score, scores.time FROM scores JOIN players ON scores.player_id = players.id ORDER BY scores.score DESC, scores.time ASC")
        leaderboard = c.fetchall()
        conn.close()
        return jsonify(leaderboard)
    except Exception as e:
        conn.close()
        return jsonify([])  # Return an empty list if there's an error

if __name__ == '__main__':
    init_db()  # Reinitialize the database
    app.run(debug=True)
