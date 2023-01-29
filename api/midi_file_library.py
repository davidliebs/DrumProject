from mido import MidiFile, tempo2bpm

note_to_drum_map = {
	51: "ride",
	49: "crash",
	47: "high-tom",
	45: "mid-tom",
	41: "floor-tom",
	42: "closed hi-hat",
	38: "snare",
	40: "snare",
	35: "bass drum"
}

def return_formatted_midi_notes(filepath):
	mid = MidiFile(filepath)

	midi_notes = {}
	formatted_midi_notes = []

	time_since_started = 0
	for i in mid:
		if i.type == "time_signature":
			time_signature_numerator = i.numerator
			time_signature_denominator = i.denominator

		elif i.type == "set_tempo":
			midi_bpm = round(tempo2bpm(i.tempo), 0)

		elif i.type == "note_on" and i.velocity == 0:
			time_since_started += i.time * 1000

			if midi_notes.get(time_since_started, False):
				midi_notes[time_since_started].append(note_to_drum_map[i.note])
			else:
				midi_notes[time_since_started] = [(note_to_drum_map[i.note])]

	for i in midi_notes:
		formatted_midi_notes.append({"timestamp": i, "notes": midi_notes[i]})
	
	time_interval = (60000/midi_bpm) / (time_signature_denominator/4)

	return {"musicData": formatted_midi_notes, 
			"bpm": midi_bpm,
			"timeSignatureNumerator": time_signature_numerator,
			"timeSignatureDenominator": time_signature_denominator,
			"timeInterval": time_interval
	}