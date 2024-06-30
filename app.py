from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit
import time

app = Flask(__name__)
socketio = SocketIO(app)

# In-memory storage for notes
notes = []

# Sample users storage (for demonstration)
users = {}

# Route to render the map and notes form
@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notes Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
        #map { height: 400px; }
        .container { width: 80%; margin: 0 auto; padding: 20px; }
        .form-container { position: fixed; bottom: 20px; right: 20px; background-color: #fff; padding: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
        form { display: flex; flex-direction: column; }
        input, textarea { margin-bottom: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        button { padding: 10px; background-color: #007bff; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        #notes-list { margin-top: 20px; }
        .note { border: 1px solid #ddd; padding: 10px; border-radius: 4px; margin-bottom: 10px; }
        .note-title { font-weight: bold; }
        .note-content { margin-top: 5px; }
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="form-container">
        <h2>Add Note</h2>
        <form id="note-form">
            <input type="text" id="username" placeholder="Your Name" required>
            <textarea id="content" placeholder="Note Content" required></textarea>
            <button type="submit">Add Note</button>
        </form>
    </div>
    <div class="container">
        <h1>Notes Map</h1>
        <div id="notes-list"></div>
    </div>
    
    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.4.1/socket.io.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const socket = io();

            // Initialize map
            const map = L.map('map').setView([0, 0], 2); // Initial center and zoom level
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 18,
                attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);

            // Add note markers
            const addMarkers = (notes) => {
                notes.forEach(note => {
                    L.marker([note.latitude, note.longitude]).addTo(map)
                        .bindPopup(`<b>${note.username}</b><br>${note.content}`)
                        .openPopup();
                });
            };

            // Fetch and display existing notes
            const fetchNotes = async () => {
                const response = await fetch('/notes');
                const notes = await response.json();
                addMarkers(notes);
                renderNotes(notes);
            };

            // Render notes list
            const renderNotes = (notes) => {
                const notesList = document.getElementById('notes-list');
                notesList.innerHTML = '';
                notes.forEach(note => {
                    const noteDiv = document.createElement('div');
                    noteDiv.className = 'note';
                    noteDiv.innerHTML = `
                        <div class="note-title">${note.username}</div>
                        <div class="note-content">${note.content}</div>
                        <button onclick="deleteNote('${note.id}')">Delete</button>
                    `;
                    notesList.appendChild(noteDiv);
                });
            };

            // Handle form submission
            const form = document.getElementById('note-form');
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const username = document.getElementById('username').value;
                const content = document.getElementById('content').value;
                const { latitude, longitude } = await getLocation(); // Get current location

                const response = await fetch('/notes', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, content, latitude, longitude })
                });

                if (response.ok) {
                    fetchNotes();
                    form.reset();
                }
            });

            // Function to get current location
            const getLocation = () => {
                return new Promise((resolve, reject) => {
                    if ('geolocation' in navigator) {
                        navigator.geolocation.getCurrentPosition(position => {
                            resolve({ latitude: position.coords.latitude, longitude: position.coords.longitude });
                        }, error => {
                            console.error('Error getting location:', error);
                            alert('Error getting location. Please enable location services.');
                            reject(error);
                        });
                    } else {
                        alert('Geolocation is not supported by this browser.');
                        reject('Geolocation not supported');
                    }
                });
            };

            // Function to delete a note
            const deleteNote = async (noteId) => {
                const response = await fetch(`/notes/${noteId}`, { method: 'DELETE' });
                if (response.ok) {
                    fetchNotes();
                }
            };

            // Socket.io events
            socket.on('new_note', (note) => {
                addMarkers([note]);
                renderNotes([note]);
            });

            // Initial fetch and setup
            fetchNotes();
        });
    </script>
</body>
</html>
    ''')

# Route to handle GET and POST requests for notes
@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'GET':
        return jsonify(notes), 200
    elif request.method == 'POST':
        note_data = request.json
        username = note_data.get('username')
        # Check if user already posted a note within last 12 hours
        if username in users and (time.time() - users[username]) < 43200:  # 43200 seconds = 12 hours
            return jsonify({'error': 'You can only post one note every 12 hours.'}), 400
        note_data['id'] = len(notes) + 1  # Example: Generate unique ID for note
        notes.append(note_data)
        users[username] = time.time()  # Update user's last note timestamp
        socketio.emit('new_note', note_data)
        return jsonify(note_data), 201

# Route to delete a note
@app.route('/notes/<int:index>', methods=['DELETE'])
def delete_note(index):
    if 0 <= index < len(notes):
        deleted_note = notes.pop(index)
        return jsonify(deleted_note), 200
    else:
        return jsonify({'error': 'Note not found'}), 404

if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'your_secret_key'  # Set a secret key for session management
    socketio.run(app, host='0.0.0.0', port=5000)
        
