from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

notes = []

@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notes App</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
        #map { height: 400px; }
        .container { width: 80%; margin: 0 auto; padding: 20px; }
        h1 { text-align: center; }
        form { display: flex; flex-direction: column; margin-bottom: 20px; }
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
    <div class="container">
        <h1>Notes App</h1>
        <form id="note-form">
            <input type="text" id="username" placeholder="Your Name" required>
            <textarea id="content" placeholder="Content" required></textarea>
            <button type="submit">Add Note</button>
        </form>
        <div id="notes-list"></div>
    </div>
    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.4.1/socket.io.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const socket = io();

            // Initialize map
            const map = L.map('map').setView([51.505, -0.09], 13); // Initial center and zoom level
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 18,
                attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);

            // Add marker on map click
            map.on('click', function(e) {
                const { lat, lng } = e.latlng;
                document.getElementById('latitude').value = lat.toFixed(5);
                document.getElementById('longitude').value = lng.toFixed(5);
                L.marker([lat, lng]).addTo(map);
            });

            const form = document.getElementById('note-form');
            const notesList = document.getElementById('notes-list');

            const fetchNotes = async () => {
                const response = await fetch('/notes');
                const notes = await response.json();
                renderNotes(notes);
            };

            const renderNotes = (notes) => {
                notesList.innerHTML = '';
                notes.forEach((note, index) => {
                    const noteDiv = document.createElement('div');
                    noteDiv.className = 'note';
                    noteDiv.innerHTML = `
                        <div class="note-title">${note.username}</div>
                        <div class="note-content">${note.content}</div>
                        <div class="note-location">Lat: ${note.latitude}, Lng: ${note.longitude}</div>
                        <button onclick="deleteNote(${index})">Delete</button>
                    `;
                    notesList.appendChild(noteDiv);
                });
            };

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const username = document.getElementById('username').value;
                const content = document.getElementById('content').value;
                const latitude = document.getElementById('latitude').value;
                const longitude = document.getElementById('longitude').value;

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

            window.deleteNote = async (index) => {
                const response = await fetch(`/notes/${index}`, { method: 'DELETE' });

                if (response.ok) {
                    fetchNotes();
                }
            };

            socket.on('new_note', (note) => {
                fetchNotes();
                alert(`New note added: ${note.username}`);
            });

            fetchNotes();
        });
    </script>
</body>
</html>
    ''')

@app.route('/notes', methods=['GET'])
def get_notes():
    return jsonify(notes), 200

@app.route('/notes', methods=['POST'])
def create_note():
    note = request.json
    notes.append(note)
    socketio.emit('new_note', note)
    return jsonify(note), 201

@app.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    if 0 <= note_id < len(notes):
        note = notes.pop(note_id)
        return jsonify(note), 200
    else:
        return jsonify({'error': 'Note not found'}), 404

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
