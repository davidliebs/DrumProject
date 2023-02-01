from mido import MidiFile, tempo2bpm
from xml.dom import minidom

musescore_midi_notes_to_drum = {
	51: "ride",
	49: "crash",
	47: "high-tom",
	45: "mid-tom",
	41: "floor-tom",
	42: "closed hi-hat",
	38: "snare",
	40: "snare",
	35: "bass drum",
	36: "bass drum"
}

def return_formatted_midi_notes(midi_filepath):
	mid = MidiFile(midi_filepath)

	midi_notes = {}
	formatted_midi_notes = []

	for i in mid:
		if i.type == "time_signature":
			time_signature_numerator = i.numerator
			time_signature_denominator = i.denominator

		elif i.type == "set_tempo":
			midi_bpm = round(tempo2bpm(i.tempo), 0)

	required_data = [i for i in mid if i.type == "note_on" and i.velocity == 0]
	time_since_started = -required_data[0].time * 1000
	for i in required_data:
		time_since_started += i.time * 1000

		if midi_notes.get(time_since_started, False):
			midi_notes[time_since_started].append(musescore_midi_notes_to_drum[i.note])
		else:
			midi_notes[time_since_started] = [(musescore_midi_notes_to_drum[i.note])]

	for i in midi_notes:
		formatted_midi_notes.append({"timestamp": i, "notes": midi_notes[i]})
	
	time_interval = (60000/midi_bpm) / (time_signature_denominator/4)

	return {"musicData": formatted_midi_notes, 
			"bpm": midi_bpm,
			"timeSignatureNumerator": time_signature_numerator,
			"timeSignatureDenominator": time_signature_denominator,
			"timeInterval": time_interval
	}

def return_svg_indexes(svg_filepath):
	doc = minidom.parse(svg_filepath)
	path_transform_strings = [path.getAttribute('transform') for path in doc.getElementsByTagName('path') if path.getAttribute("class")=="Note"]

	svg_index_dict = {}
	for index, i in enumerate(path_transform_strings):
		if i == '':
			continue

		position_on_page = float(i.split(",")[4])
		# svg_index_dict[index] = position_on_page
		if not svg_index_dict.get(position_on_page, False):
			svg_index_dict[position_on_page] = [index]

		else:
			svg_index_dict[position_on_page].append(index)

	svg_index_list = []
	for i in (sorted(list(svg_index_dict.keys()))):
		svg_index_list.append(svg_index_dict[i])
	
	return svg_index_list