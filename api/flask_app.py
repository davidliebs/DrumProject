from flask import Flask, render_template, jsonify
from flask_cors import CORS
import json
import midi_file_library

app = Flask(__name__)
CORS(app)

@app.route("/request_music_notation_data")
def request_music_notation_data():
	music_notation_data, bpm, time_signature_numerator, time_signature_denominator = midi_file_library.return_formatted_midi_notes("./media/challenge1.mid")

	return jsonify([music_notation_data, bpm, time_signature_numerator, time_signature_denominator])

@app.route("/request_midi_notes_to_drum_name")
def request_midi_notes_to_drum_name():
	data = {
		40: "snare",
		48: "high-tom",
		45: "mid-tom",
		43: "floor-tom",
		55: "crash",
		49: "crash",
		52: "crash 2",
		57: "crash 2",
		51: "ride",
		59: "ride"
	}

	return jsonify(data)

app.run(port=5000, debug=True)