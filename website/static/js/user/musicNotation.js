class Music{
	constructor(music_data, beats_per_measure, time_interval, midi_notes_to_drum_name, svgIndexes) {
		this.music_data = music_data;
		this.midi_notes_to_drum_name = midi_notes_to_drum_name;
		this.beats_per_measure = beats_per_measure;
		this.time_interval = time_interval;
		this.notes_played = [];
		this.recording = false;
		this.challenge_played_correctly = true;
		this.svgIndexes = svgIndexes
	}

	start(timestamp_button_clicked) {
		this.start_challenge_time = timestamp_button_clicked + this.beats_per_measure * this.time_interval;
		this.recording = true;
	}

	updateMusic(timestamp, midiData) {
		let initialLength = this.notes_played.length;

		if (this.notes_played.length === 0) {
			this.notes_played.push([{"timestamp": timestamp, "note": midiData[1]}]);
			return false;
		}
		else if (this.notes_played[this.notes_played.length-1][0]["timestamp"]+90 > timestamp) {
			this.notes_played[this.notes_played.length-1].push({"timestamp": timestamp, "note": midiData[1]});

		} else {
			this.notes_played.push([{"timestamp": timestamp, "note": midiData[1]}]);
		}

		if (initialLength != this.notes_played.length) {
			if (this.notes_played.length >= this.music_data.length+1) {
				this.recording = false;
			}

			return this.returnDataToUpdateSvg();
		}

		return false;
	}

	returnDataToUpdateSvg() {
		const index = this.notes_played.length - 2;

		const svgElementIndexes = this.svgIndexes[index];
		const lastNote = this.notes_played[index];

		const timeNoteWasHit = lastNote[0]["timestamp"] - this.start_challenge_time;
		const timeDelay = Math.abs(timeNoteWasHit - this.music_data[index]["timestamp"]);

		if (timeDelay > 300) {
			// update svg orange
			this.challenge_played_correctly = false;
			return [svgElementIndexes, "orange"];
		}

		// update svg red
		let drums_hit = lastNote.map(x => this.midi_notes_to_drum_name[x["note"]]).sort();

		if (JSON.stringify(drums_hit) != JSON.stringify(this.music_data[index]["notes"].sort())) {
			this.challenge_played_correctly = false;
			return [svgElementIndexes, "red"]
		}

		// update svg green
		return [svgElementIndexes, "#23CE6B"];
	}

	restart() {
		this.notes_played = [];
		this.challenge_played_correctly = true;
	}
}

export default Music;