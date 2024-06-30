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
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f8f9fa; }
        .container { width: 50%; margin: 0 auto; padding: 20px; background-color: #ffffff; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
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
    <div class="container">
        <h1>Notes App</h1>
        <form id="note-form">
            <input type="text" id="title" placeholder="Title" required>
            <textarea id="content" placeholder="Content" required></textarea>
            <button type="submit">Add Note</button>
        </form>
        <div id="notes-list"></div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.4.1/socket.io.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const socket = io();

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
                        <div class="note-title">${note.title}</div>
                        <div class="note-content">${note.content}</div>
                        <button onclick="deleteNote(${index})">Delete</button>
                    `;
                    notesList.appendChild(noteDiv);
                });
            };

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const title = document.getElementById('title').value;
                const content = document.getElementById('content').value;

                const response = await fetch('/notes', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, content })
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
                alert(`New note added: ${note.title}`);
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

@app.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    if 0 <= note_id < len(notes):
        return jsonify(notes[note_id]), 200
    else:
        return jsonify({'error': 'Note not found'}), 404

@app.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    if 0 <= note_id < len(notes):
        note = request.json
        notes[note_id] = note
        return jsonify(note), 200
    else:
        return jsonify({'error': 'Note not found'}), 404

@app.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    if 0 <= note_id < len(notes):
        note = notes.pop(note_id)
        return jsonify(note), 200
    else:
        return jsonify({'error': 'Note not found'}), 404

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
           
