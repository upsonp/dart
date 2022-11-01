var synth = window.speechSynthesis;
var pitch = 1;
var rate = 1;
var volume = 1;
var voices = [];

function populateVoiceList() {
  voices = synth.getVoices();
}

function speak(playbackString) {
  populateVoiceList();
  var msg = new SpeechSynthesisUtterance();
  msg.volume = volume; // 0 to 1
  msg.rate = rate; // 0.1 to 10
  msg.pitch = pitch; //0 to 2
  msg.text = playbackString;
  msg.lang = 'en-US';
  // msg.voice = voices[3];
  speechSynthesis.speak(msg);
}

function parle(playbackString) {
  populateVoiceList();
  var msg = new SpeechSynthesisUtterance();
  msg.volume = volume; // 0 to 1
  msg.rate = rate; // 0.1 to 10
  msg.pitch = pitch; //0 to 2
  msg.text = playbackString;
  msg.lang = 'fr-CA';
  // msg.voice = voices[8];
  speechSynthesis.speak(msg);
}

// function parle(playbackString) {
//   console.log(speechSynthesis.getVoices());
//   var msg = new SpeechSynthesisUtterance();
//   var voices = window.speechSynthesis.getVoices();
//   console.log(voices);
//   // msg.voice = voices[0]; // Note: some voices don't support altering params
//   msg.voiceURI = 'native';
//   msg.volume = 1; // 0 to 1
//   msg.rate = 1; // 0.1 to 10
//   msg.pitch = 1; //0 to 2
//   msg.text = playbackString;
//   msg.lang = 'fr-CA';
//   speechSynthesis.speak(msg);
// }
