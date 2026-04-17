<template>
  <div class="desktop-bg">
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <div class="blob blob-3"></div>
  </div>
</template>

<style scoped lang="scss">
.desktop-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #e8f4fc 0%, #d0e6f4 100%);
  overflow: hidden;
  z-index: var(--z-background);
}

.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.6;
  mix-blend-mode: screen;
}

.blob-1 {
  width: 60vw; height: 60vw;
  background: radial-gradient(circle, #b0d4ec 0%, transparent 70%);
  top: -20vw; left: -10vw;
  animation: float-1 50s ease-in-out infinite;
}

.blob-2 {
  width: 50vw; height: 50vw;
  background: radial-gradient(circle, #a0c8e0 0%, transparent 70%);
  top: 30vh; right: -15vw;
  animation: float-2 60s ease-in-out infinite;
}

.blob-3 {
  width: 40vw; height: 40vw;
  background: radial-gradient(circle, #c8dff0 0%, transparent 70%);
  bottom: -10vw; left: 20vw;
  animation: float-3 55s ease-in-out infinite;
}

@keyframes float-1 {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  50% { transform: translate(10vw, 8vh) rotate(180deg); }
}
@keyframes float-2 {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  50% { transform: translate(-12vw, -10vh) rotate(-180deg); }
}
@keyframes float-3 {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  50% { transform: translate(8vw, -12vh) rotate(90deg); }
}
</style>
