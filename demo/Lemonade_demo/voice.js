/**
 * Slide narration via the Web Speech API (browser text-to-speech).
 * No audio files required. Skips if speechSynthesis is unavailable.
 */
(function (global) {
  "use strict";

  function pickEnglishVoice() {
    var list = global.speechSynthesis.getVoices();
    if (!list || !list.length) return null;
    var i;
    for (i = 0; i < list.length; i++) {
      if (list[i].lang && /^en-US/i.test(list[i].lang)) return list[i];
    }
    for (i = 0; i < list.length; i++) {
      if (list[i].lang && /^en/i.test(list[i].lang)) return list[i];
    }
    return list[0];
  }

  /**
   * @param {string} text - Words to speak
   * @param {{ delayMs?: number, rate?: number, lang?: string }} [options]
   */
  global.playSlideNarration = function (text, options) {
    options = options || {};
    if (!global.speechSynthesis || !text) return;

    var delayMs = options.delayMs != null ? options.delayMs : 380;

    function speak() {
      global.speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(text);
      u.lang = options.lang || "en-US";
      u.rate = options.rate != null ? options.rate : 0.92;
      u.pitch = options.pitch != null ? options.pitch : 1;
      u.volume = options.volume != null ? options.volume : 1;
      var voice = pickEnglishVoice();
      if (voice) u.voice = voice;
      global.speechSynthesis.speak(u);
    }

    function schedule() {
      setTimeout(speak, delayMs);
    }

    if (global.speechSynthesis.getVoices().length === 0) {
      global.speechSynthesis.addEventListener("voiceschanged", function once() {
        global.speechSynthesis.removeEventListener("voiceschanged", once);
        schedule();
      });
    } else {
      schedule();
    }
  };

  global.stopSlideNarration = function () {
    if (global.speechSynthesis) global.speechSynthesis.cancel();
  };

  global.addEventListener("beforeunload", function () {
    global.stopSlideNarration();
  });
})(typeof window !== "undefined" ? window : this);
