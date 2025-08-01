(() => {
  const storage = window.localStorage;
  const ENABLED = 'bgmEnabled';
  const TIME = 'bgmTime';

  function init() {
    const audio = document.getElementById('bgm');
    if (!audio) {
      return;
    }

    if (storage.getItem(ENABLED) === null) {
      storage.setItem(ENABLED, 'true');
    }
    const enabled = storage.getItem(ENABLED) === 'true';

    const start = parseFloat(storage.getItem(TIME)) || 0;
    audio.volume = 0.5;

    function resume() {
      if (!isNaN(start)) {
        audio.currentTime = start;
      }
      if (enabled) {
        audio.play().catch(() => {});
      }
    }

    if (audio.readyState >= 1) {
      resume();
    } else {
      audio.addEventListener('loadedmetadata', resume, { once: true });
    }

    audio.addEventListener('timeupdate', () => {
      storage.setItem(TIME, audio.currentTime);
    });

    window.addEventListener('beforeunload', () => {
      storage.setItem(TIME, audio.currentTime);
    });
  }

  document.addEventListener('DOMContentLoaded', init);

  window.setBgmEnabled = function(flag) {
    storage.setItem(ENABLED, flag ? 'true' : 'false');
    const audio = document.getElementById('bgm');
    if (!audio) {
      return;
    }
    if (flag) {
      const start = parseFloat(storage.getItem(TIME)) || 0;
      if (!isNaN(start)) {
        audio.currentTime = start;
      }
      audio.play().catch(() => {});
    } else {
      audio.pause();
    }
  };
})();
