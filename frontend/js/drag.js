document.addEventListener('DOMContentLoaded', () => {
  const chatPanel = document.getElementById('chat-panel');
  const chatHeader = document.querySelector('.chat-header');
  const chatToggle = document.getElementById('chat-toggle');

  if (!chatPanel || !chatHeader || !chatToggle) return;

  // ==========================================
  // CHAT PANEL DRAG
  // ==========================================

  let draggingPanel = false;
  let panelOffsetX = 0;
  let panelOffsetY = 0;

  chatHeader.addEventListener('mousedown', (event) => {
    // New Chat button ko drag handle na banao
    if (event.target.closest('#new-chat-button')) return;

    draggingPanel = true;

    const rect = chatPanel.getBoundingClientRect();

    panelOffsetX = event.clientX - rect.left;
    panelOffsetY = event.clientY - rect.top;

    chatPanel.style.right = 'auto';
    chatPanel.style.bottom = 'auto';
    chatPanel.style.left = `${rect.left}px`;
    chatPanel.style.top = `${rect.top}px`;

    chatHeader.style.cursor = 'grabbing';

    event.preventDefault();
  });

  // ==========================================
  // FLOATING BUTTON DRAG
  // ==========================================

  let draggingToggle = false;
  let toggleOffsetX = 0;
  let toggleOffsetY = 0;

  chatToggle.addEventListener('mousedown', (event) => {
    draggingToggle = true;

    const rect = chatToggle.getBoundingClientRect();

    toggleOffsetX = event.clientX - rect.left;
    toggleOffsetY = event.clientY - rect.top;

    // Right/bottom ko remove karke exact position set karo
    chatToggle.style.right = 'auto';
    chatToggle.style.bottom = 'auto';

    chatToggle.style.left = `${rect.left}px`;
    chatToggle.style.top = `${rect.top}px`;

    chatToggle.style.cursor = 'grabbing';

    event.preventDefault();
  });

  // ==========================================
  // MOUSE MOVE
  // ==========================================

  document.addEventListener('mousemove', (event) => {

    // PANEL MOVE
    if (draggingPanel) {
      let newLeft = event.clientX - panelOffsetX;
      let newTop = event.clientY - panelOffsetY;

      const maxLeft =
        window.innerWidth - chatPanel.offsetWidth;

      const maxTop =
        window.innerHeight - chatPanel.offsetHeight;

      newLeft = Math.max(0, Math.min(newLeft, maxLeft));
      newTop = Math.max(0, Math.min(newTop, maxTop));

      chatPanel.style.left = `${newLeft}px`;
      chatPanel.style.top = `${newTop}px`;
    }

    // BUTTON MOVE
    if (draggingToggle) {
      let newLeft = event.clientX - toggleOffsetX;
      let newTop = event.clientY - toggleOffsetY;

      const maxLeft =
        window.innerWidth - chatToggle.offsetWidth;

      const maxTop =
        window.innerHeight - chatToggle.offsetHeight;

      newLeft = Math.max(0, Math.min(newLeft, maxLeft));
      newTop = Math.max(0, Math.min(newTop, maxTop));

      chatToggle.style.left = `${newLeft}px`;
      chatToggle.style.top = `${newTop}px`;
    }
  });

  // ==========================================
  // MOUSE UP
  // ==========================================

  document.addEventListener('mouseup', () => {

    if (draggingPanel) {
      draggingPanel = false;
      chatHeader.style.cursor = 'grab';
    }

    if (draggingToggle) {
      draggingToggle = false;
      chatToggle.style.cursor = 'grab';
    }
  });

  // Initial cursors
  chatHeader.style.cursor = 'grab';
  chatToggle.style.cursor = 'grab';
});