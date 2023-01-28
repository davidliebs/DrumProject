import Timer from './timer.js';
import Music from './musicNotation.js';

var metronomeCount = 0;
const click1 = new Audio('/static/media/click1.mp3');
const click2 = new Audio('/static/media/click2.mp3');

// fetching music notation data
async function fetchMusicNotationData() {
	const result = await $.ajax({
		url: "http://localhost:5000/request_music_notation_data",
		data: {
			challengeId: challengeId
		},
		type: 'GET'
	});

	const musicData = result[0];
	const bpm = result[1];
	const timeSignatureNumerator = result[2];
	const timeSignatureDenominator = result[3];
	const timeInterval = (60000/bpm) / (timeSignatureDenominator/4);	

	return {"musicData": musicData, "bpm": bpm, "timeSignatureNumerator": timeSignatureNumerator, "timeSignatureDenominator": timeSignatureDenominator, "timeInterval": timeInterval};
}
const musicNotationData = await fetchMusicNotationData();

// fetching midi notes to drum name
async function fetchMidiNotesToDrumName() {
	const result = await $.ajax({
		url: "http://localhost:5000/request_midi_notes_to_drum_name",
		type: 'GET',
	});

	return result;
}
const midiNotesToDrumName = await fetchMidiNotesToDrumName();

function changeColorOfIndex(svgPaths, index, colorToChangeTo) {
	svgPaths[index].setAttribute("fill", colorToChangeTo);
}

function playClick() {
	if (metronomeCount == musicNotationData["timeSignatureNumerator"]) {
		metronomeCount = 0;
	}
	if (metronomeCount == 0) {
		click1.play();
		click1.currentTime = 0;
	} else {
		click2.play();
		click2.currentTime = 0;
	}
	metronomeCount++;
}

$(document).ready(function() {
	var svgMusicFile = document.getElementById("musicSvgFile");
	var svgDoc = svgMusicFile.contentDocument;
	var svgPaths = svgDoc.querySelectorAll("path.Note");

	const metronome = new Timer(playClick, musicNotationData["timeInterval"], { immediate: true });
	var musicNotation = new Music(musicNotationData["musicData"], musicNotationData["timeSignatureNumerator"], musicNotationData["timeInterval"], midiNotesToDrumName, svgPaths);

	// MIDI handling
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
		if (!musicNotation.recording) {
			return;
		}

		if (midiData.data[0] === 153 || midiData.data[0] === 144) {
			const dataForSvg = musicNotation.updateMusic(Date.now(), midiData.data);

			if (dataForSvg) {
				const indexesToUpdate = dataForSvg[0];
				const colour = dataForSvg[1];
				for (let x = 0; x < indexesToUpdate.length; x++) {
					changeColorOfIndex(svgPaths, indexesToUpdate[x], colour);
				}
			}

			if (!musicNotation.recording) {
				$("#toggleMetronomeButton").trigger("click");
			}
		}
	}

	function failure() {
		console.log("MIDI access failure");
	}

	$("#toggleMetronomeButton").click(function() {
		metronomeCount = 0;
		// starting metronome
		if ($("#toggleMetronomeButton").text() == "Start") {
			metronome.start();
			musicNotation.start(Date.now());
			$("#toggleMetronomeButton").text("Stop");
		
		// stopping metronome
		} else {
			metronome.stop();
			$("#toggleMetronomeButton").text("Start");
			musicNotation.restart();
		}
	});
});