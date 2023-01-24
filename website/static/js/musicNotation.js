class Music{
	constructor(music_data, beats_per_measure, time_interval, midi_notes_to_drum_name) {
		this.music_data = music_data;
		this.midi_notes_to_drum_name = midi_notes_to_drum_name;
		this.beats_per_measure = beats_per_measure;
		this.time_interval = time_interval;
		this.notes_played = [];
	}

	start(timestamp_button_clicked) {
		this.start_challenge_time = timestamp_button_clicked + this.beats_per_measure * this.time_interval;
	}

	update_music(timestamp, midiData){		
		// checking if this note was played together with the last one
		if (this.notes_played.length === 0) {
			this.notes_played.push([{"timestamp": timestamp, "note": midiData[1]}]);
		} 
		
		else if (this.notes_played[this.notes_played.length-1][0]["timestamp"]+90 > timestamp) {
			this.notes_played[this.notes_played.length-1].push({"timestamp": timestamp, "note": midiData[1]});

		} else {
			this.notes_played.push([{"timestamp": timestamp, "note": midiData[1]}]);
		}
	}

	finish() {
		// check the music notation and the notes played are the same length
		if (this.notes_played.length != this.music_data.length){
			return "incorrect amount of strokes";
		}

		let incorrectFlag = false;
		let reason;

		this.notes_played.forEach(function(value, index){ 
			let time_note_was_hit = value[0]["timestamp"] - this.start_challenge_time;
			const time_delay = Math.abs(time_note_was_hit - this.music_data[index]["timestamp"]);

			if (time_delay > 200) {
				incorrectFlag = true;
				reason = "out of time";
			}

			let drums_hit = value.map(x => this.midi_notes_to_drum_name[x["note"]]).sort();

			if (JSON.stringify(drums_hit) != JSON.stringify(this.music_data[index]["notes"].sort())) {
				incorrectFlag = true;
				reason = "wrong drums hit";
			}

		}, this);

		if (incorrectFlag) {
			return "Incorrect ".concat(reason);
		}
		
		return "Correct";
	}

	clear() {
		this.notes_played = []
	}
}

export default Music;