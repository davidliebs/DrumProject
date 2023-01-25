class Music{
	constructor(music_data, beats_per_measure, time_interval, midi_notes_to_drum_name, musicSvgPaths) {
		this.music_data = music_data;
		this.midi_notes_to_drum_name = midi_notes_to_drum_name;
		this.beats_per_measure = beats_per_measure;
		this.time_interval = time_interval;
		this.notes_played = [];
		this.createIndexesList();
	}

	createIndexesList() {
		this.svgIndexes = [];
		let svgIndex = 0
		for (let index in this.music_data) {
			let tempList = [];
			let notes = this.music_data[index]["notes"];
			for (let x = 0; x < notes.length; x++) {
				tempList.push(svgIndex);
				svgIndex ++;
			}
		this.svgIndexes.push(tempList);
		}
	}

	start(timestamp_button_clicked) {
		this.start_challenge_time = timestamp_button_clicked + this.beats_per_measure * this.time_interval;
	}

	updateMusic(timestamp, midiData) {
		let initialLength = this.notes_played.length;

		if (this.notes_played.length === 0) {
			this.notes_played.push([{"timestamp": timestamp, "note": midiData[1]}]);
			return;
		}
		else if (this.notes_played[this.notes_played.length-1][0]["timestamp"]+90 > timestamp) {
			this.notes_played[this.notes_played.length-1].push({"timestamp": timestamp, "note": midiData[1]});

		} else {
			this.notes_played.push([{"timestamp": timestamp, "note": midiData[1]}]);
		}

		if (initialLength != this.notes_played.length) {
			return this.returnDataToUpdateSvg();
		}

		return false;
	}

	returnDataToUpdateSvg() {
		const index = this.notes_played.length - 2;

		const svgElementIndexes = this.svgIndexes[index];
		const lastNote = this.notes_played[index]

		const timeNoteWasHit = lastNote[0]["timestamp"] - this.start_challenge_time;
		const timeDelay = Math.abs(timeNoteWasHit - this.music_data[index]["timestamp"]);

		if (timeDelay > 200) {
			// update svg orange
			return [svgElementIndexes, "orange"];
		}

		// update svg red
		let drums_hit = lastNote.map(x => this.midi_notes_to_drum_name[x["note"]]).sort();

		if (JSON.stringify(drums_hit) != JSON.stringify(this.music_data[index]["notes"].sort())) {
			return [svgElementIndexes, "red"]
		}

		// update svg green
		return [svgElementIndexes, "green"];
	}
}

export default Music;