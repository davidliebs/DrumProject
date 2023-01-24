import Timer from './timer.js';
import Music from './musicNotation.js';

const click1 = new Audio('/static/media/click1.mp3');
const click2 = new Audio('/static/media/click2.mp3');
const toggleMetronomeButton = document.querySelector('.toggleMetronomeButton');

// const timeInterval = (60000/bpm) / (Number(timeSignature.split("/")[1])/4);
let count = 0;

// INITIALISATION
async function fetch_music_data() {
	const res = await fetch("http://localhost:5000/request_music_notation_data")	
	return res.json()
}

const data_returned = await fetch_music_data();
const music_data = data_returned[0];
const bpm = data_returned[1];
const timgSignatureNumerator = data_returned[2];
const timgSignatureDenominator = data_returned[3];
const timeInterval = (60000/bpm) / (timgSignatureDenominator/4);

console.log(bpm);

async function fetch_midi_to_drum_notes() {
	const res = await fetch("http://localhost:5000/request_midi_notes_to_drum_name")
	return res.json()
}

const midi_notes_to_drum_name = await fetch_midi_to_drum_notes()

const musicNotation = new Music(music_data, timgSignatureNumerator, timeInterval, midi_notes_to_drum_name);

// REQUESTING MIDI ACCESS
if (navigator.requestMIDIAccess) {
	navigator.requestMIDIAccess().then(success, failure);
}

function success(MIDIAccess) {
	const inputs = MIDIAccess.inputs;
	inputs.forEach((input) => {
		input.addEventListener("midimessage", handleInput);
	})
}

function handleInput(midiData) {
	if (midiData.data[0] === 153 || midiData.data[0] === 144) {
		musicNotation.update_music(Date.now(), midiData.data);
	}
}

function failure() {
	console.log("MIDI access failure");
}

// METRONOME
toggleMetronomeButton.addEventListener('click', () => {
	count = 0;
	// starting metronome
	if (toggleMetronomeButton.textContent === "Start") {
		metronome.start();
		musicNotation.clear();
		musicNotation.start(Date.now());
		toggleMetronomeButton.textContent = 'Stop';
	
	// stopping metronome
	} else {
		metronome.stop();
		alert(musicNotation.finish());
		toggleMetronomeButton.textContent = 'Start';
	}
});

function playClick() {
	if (count === timgSignatureNumerator) {
		count = 0;
	}
	if (count === 0) {
		click1.play();
		click1.currentTime = 0;
	} else {
		click2.play();
		click2.currentTime = 0;
	}
	count++;
}

const metronome = new Timer(playClick, timeInterval, { immediate: true });