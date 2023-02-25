import Timer from './timer.js';
import Music from './musicNotation.js';

var metronomeCount = 0;
const click1 = new Audio('/static/media/challenge-files/click1.mp3');
const click2 = new Audio('/static/media/challenge-files/click2.mp3');
const successSound = new Audio('/static/media/challenge-files/success-sound.mp3')

function changeColorOfIndex(svgPaths, index, colorToChangeTo) {
	svgPaths[index].setAttribute("fill", colorToChangeTo);
}

function resetSvg(svgPaths) {
	for (let index = 0; index < svgPaths.length; index++) {
		svgPaths[index].setAttribute("fill", "black");
	}
}

let startDrumming = false;
function playClick() {
	if (metronomeCount == musicNotationData["timeSignatureNumerator"]) {
		metronomeCount = 0;
		startDrumming = true;
	}
	if (metronomeCount == 0) {
		click1.play();
		click1.currentTime = 0;
	} else {
		click2.play();
		click2.currentTime = 0;
	}
	if (!startDrumming) {
		$("#metronomeDisplay").text(metronomeCount+1);
		$("#metronomeDisplay").css("color", "gray")
	} else {
		$("#metronomeDisplay").css("color", "#ffffff")
		$("#metronomeDisplay").text(metronomeCount+1);
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

		if (midiData.data[2] < 12) {
			return;
		}

		if (midiData.data[0] === 153 || midiData.data[0] === 144) {
			const dataForSvg = musicNotation.updateMusic(Date.now(), midiData.data);

			if (dataForSvg) {
				for (let x=0; x < dataForSvg.length; x++) {
					let indexesToUpdate = dataForSvg[x][0];
					let svgColour = dataForSvg[x][1];

					if (indexesToUpdate) {
						if (indexesToUpdate[0] < svgPaths.length) {
							for (let y = 0; y < indexesToUpdate.length; y++) {
								changeColorOfIndex(svgPaths, indexesToUpdate[y], svgColour);
							}
						}
					}
				}
			}

			if (!musicNotation.recording) {
				if (musicNotation.challenge_played_correctly) {
					successSound.play();
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

			for (let x = 0; x < svgIndexes[0].length; x++) {
				changeColorOfIndex(svgPaths, svgIndexes[0][x], "#3763f4");
			}

		// stopping metronome
		} else {
			metronome.stop();
			$("#toggleMetronomeButton").text("Start");
			musicNotation.restart();
			startDrumming = false;
		}
	});

	$("#moveToNextChallengeButton").click(function() {
		window.location.replace(`/user/next_challenge?courseID=${courseID}&challengeID=${challengeID}`);
	})
});