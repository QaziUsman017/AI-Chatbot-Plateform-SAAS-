(function () {
  "use strict";

  function formatBotResponse(text) {

    if (!text) {
      return "";
    }

    let formatted = String(text);

    formatted = formatted
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    formatted = formatted.replace(
      /&lt;br\s*\/?&gt;|&lt;br/gi,
      "<br>"
    );

    formatted = formatted.replace(
      /\*\*(.*?)\*\*/g,
      "<strong>$1</strong>"
    );

    formatted = formatted.replace(
      /^### (.*)$/gm,
      "<h4>$1</h4>"
    );

    formatted = formatted.replace(
      /^## (.*)$/gm,
      "<h3>$1</h3>"
    );

    formatted = formatted.replace(
      /^# (.*)$/gm,
      "<h2>$1</h2>"
    );

    formatted = formatted.replace(
      /^[•\-] (.*)$/gm,
      "• $1"
    );

    formatted = formatted.replace(
      /\n/g,
      "<br>"
    );

    formatted = formatted.replace(
      /\\\|/g,
      "|"
    );

    return formatted;
  }


  window.ui = {

    addMessage(text, role = "bot") {

      const chatWindow =
        document.getElementById("chat-window");

      if (!chatWindow) {
        return;
      }

      const message =
        document.createElement("div");

      message.className =
        `message ${role}`;

      const messageText =
        document.createElement("div");

      if (role === "bot") {

        messageText.innerHTML =
          formatBotResponse(text);

      } else {

        messageText.textContent =
          text;

      }

      const timestamp =
        document.createElement("span");

      timestamp.className =
        "message-time";

      timestamp.textContent =
        new Date().toLocaleTimeString(
          [],
          {
            hour: "2-digit",
            minute: "2-digit",
          }
        );

      message.appendChild(messageText);
      message.appendChild(timestamp);

      chatWindow.appendChild(message);

      requestAnimationFrame(() => {

        chatWindow.scrollTop =
          chatWindow.scrollHeight;

      });

    },

  };

})();