import Timer from './timer.js';
import Music from './musicNotation.js';

var metronomeCount = 0;
const click1 = new Audio('/static/media/click1.mp3');
const click2 = new Audio('/static/media/click2.mp3');

function changeColorOfIndex(svgPaths, index, colorToChangeTo) {
	svgPaths[index].setAttribute("fill", colorToChangeTo);
}

function resetSvg(svgPaths) {
	for (let index = 0; index < svgPaths.length; index++) {
		svgPaths[index].setAttribute("fill", "black");
	}
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

$(window).on("load", function() {
	var svgMusicFile = document.getElementById("musicSvgFile");
	var svgDoc = svgMusicFile.contentDocument;
	var svgPaths = svgDoc.querySelectorAll("path.Note");

	const metronome = new Timer(playClick, musicNotationData["timeInterval"], { immediate: true });
	var musicNotation = new Music(musicNotationData["musicData"], musicNotationData["timeSignatureNumerator"], musicNotationData["timeInterval"], midiNotesToDrumName, svgIndexes);

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
				if (musicNotation.challenge_played_correctly) {
					$("#moveToNextChallengeButton").prop("disabled", false);
					$("#moveToNextChallengeButton").css("background-color", getComputedStyle(document.documentElement).getPropertyValue('--secondary-color'));
					$("#moveToNextChallengeButton").css("border-color", getComputedStyle(document.documentElement).getPropertyValue('--secondary-color'));
				}
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
			resetSvg(svgPaths);
			$("#toggleMetronomeButton").text("Stop");
		
		// stopping metronome
		} else {
			metronome.stop();
			$("#toggleMetronomeButton").text("Start");
			musicNotation.restart();
		}
	});

	$("#moveToNextChallengeButton").click(function() {
		window.location.replace(`/user/next_challenge?courseID=${courseID}&challengeID=${challengeID}`);
	})
});