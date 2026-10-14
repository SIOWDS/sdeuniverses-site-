// Keep the alternative listening and watching modes from speaking at once.
(() => {
  const players = document.querySelectorAll('#video-guide video, #video-guide audio');
  players.forEach(player => player.addEventListener('play', () => {
    players.forEach(other => { if (other !== player) other.pause(); });
  }));
})();
