let note = 0;
let currentDrumsIndex = 0;

$("document").ready(function () {
	if (navigator.requestMIDIAccess) {
		navigator.requestMIDIAccess().then(midiSuccess, midiFailure);
	}

	function midiSuccess(MIDIAccess) {
		const inputs = MIDIAccess.inputs;
		inputs.forEach((input) => {
			input.addEventListener("midimessage", handleInput);
		})
	}

	function midiFailure() {
		console.log("No MIDI access allowed");
	}

	function handleInput(midiData) {
		if (midiData.data[0] != 153 && midiData.data[0] != 144) {
			return;
		}

		note = midiData.data[1];
		$("#input-"+drums[currentDrumsIndex][1]).val(note);

		currentDrumsIndex ++;
		if (currentDrumsIndex >= drums.length) {
			$("#submitButtonRow").fadeIn()
		} else {
			$("#"+drums[currentDrumsIndex][1]).fadeIn()
		}
	}

	$("#addDrumKitButton").click(function(){
		if ($("#addDrumKitButton").text() == "Add drum kit") {
			$("#addDrumKitForm").show()
			$("#addDrumKitButton").text("remove");
			$("#calibrationHeading").hide();
			$("#"+drums[currentDrumsIndex][1]).fadeIn();

		} else {
			for (let i=0; i < drums.length; i++) {
				$("#"+drums[i][1]).hide();
			}

			currentDrumsIndex = 0;
			$("#submitButtonRow").hide();
			$("#addDrumKitForm").hide();
			$("#addDrumKitButton").text("Add drum kit");
			$("#calibrationHeading").show();
		}
	});
});