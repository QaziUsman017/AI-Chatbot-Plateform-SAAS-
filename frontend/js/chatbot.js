document.addEventListener("DOMContentLoaded", () => {

  "use strict";


  // ======================================================
  // DOM ELEMENTS
  // ======================================================

  const form =
    document.getElementById("chat-form");

  const input =
    document.getElementById("message-input");

  const chatPanel =
    document.getElementById("chat-panel");

  const chatToggle =
    document.getElementById("chat-toggle");

  const newChatButton =
    document.getElementById("new-chat-button");

  const minimizeButton =
    document.getElementById("minimize-button");

  const closeButton =
    document.getElementById("close-button");

  const chatWindow =
    document.getElementById("chat-window");

  const welcomeScreen =
    document.getElementById("welcome-screen");

  const typingIndicator =
    document.getElementById("typing-indicator");

  const sendButton =
    document.getElementById("send-button");

  const suggestions =
    document.querySelectorAll(".suggestion");

  const chatHistoryList =
    document.getElementById("chat-history-list");


  // ======================================================
  // UPLOAD ELEMENTS
  // ======================================================

  const uploadButton =
    document.getElementById("upload-button");

  const documentInput =
    document.getElementById("document-input");

  const uploadStatus =
    document.getElementById("upload-status");


  // ======================================================
  // BASIC VALIDATION
  // ======================================================

  if (
    !form ||
    !input ||
    !chatPanel
  ) {

    console.error(
      "Chatbot elements not found."
    );

    return;

  }


  // ======================================================
  // AUTH
  // ======================================================

  function getAccessToken() {

    try {

      const token =
        localStorage.getItem("access_token");


      if (!token) {

        return null;

      }


      return token.trim();

    } catch (error) {

      console.error(
        "Could not read access token:",
        error
      );


      return null;

    }

  }


  function isAuthenticated() {

    return !!getAccessToken();

  }


  // ======================================================
  // CONVERSATION STATE
  // ======================================================

  let currentConversationId =
    sessionStorage.getItem(
      "chatbot_conversation_id"
    ) || null;


  function setConversationId(
    conversationId
  ) {

    currentConversationId =
      conversationId || null;


    if (currentConversationId) {

      sessionStorage.setItem(
        "chatbot_conversation_id",
        currentConversationId
      );

    } else {

      sessionStorage.removeItem(
        "chatbot_conversation_id"
      );

    }

  }


  // ======================================================
  // OPEN CHAT
  // ======================================================

  let toggleWasDragged =
    false;


  function openChat(
    focusInput = true
  ) {

    chatPanel.classList.add(
      "is-open"
    );


    chatPanel.classList.remove(
      "is-minimized"
    );


    if (chatToggle) {

      chatToggle.textContent =
        "✕";


      chatToggle.setAttribute(
        "aria-label",
        "Close chat"
      );

    }


    if (minimizeButton) {

      minimizeButton.textContent =
        "−";


      minimizeButton.setAttribute(
        "aria-label",
        "Minimize chat"
      );


      minimizeButton.setAttribute(
        "title",
        "Minimize"
      );

    }


    if (focusInput) {

      setTimeout(
        () => {

          input.focus();

        },
        100
      );

    }

  }


  // ======================================================
  // CLOSE CHAT
  // ======================================================

  function closeChat() {

    chatPanel.classList.remove(
      "is-open"
    );


    chatPanel.classList.remove(
      "is-minimized"
    );


    if (chatToggle) {

      chatToggle.textContent =
        "💬";


      chatToggle.setAttribute(
        "aria-label",
        "Open chat"
      );

    }

  }


  // ======================================================
  // CHAT TOGGLE
  // ======================================================

  if (chatToggle) {

    chatToggle.addEventListener(
      "click",
      () => {

        if (toggleWasDragged) {

          toggleWasDragged =
            false;

          return;

        }


        if (
          chatPanel.classList.contains(
            "is-open"
          )
        ) {

          closeChat();

        } else {

          openChat();

        }

      }
    );

  }


  // ======================================================
  // RESTORE MINIMIZED CHAT
  // ======================================================

  function restoreChat() {

    if (
      !chatPanel.classList.contains(
        "is-minimized"
      )
    ) {

      return;

    }


    const rect =
      chatPanel.getBoundingClientRect();


    const savedLeft =
      rect.left;


    const savedBottom =
      window.innerHeight -
      rect.bottom;


    chatPanel.style.left =
      `${savedLeft}px`;


    chatPanel.style.right =
      "auto";


    chatPanel.style.bottom =
      `${savedBottom}px`;


    chatPanel.style.top =
      "auto";


    chatPanel.classList.remove(
      "is-minimized"
    );


    if (minimizeButton) {

      minimizeButton.textContent =
        "−";


      minimizeButton.setAttribute(
        "aria-label",
        "Minimize chat"
      );


      minimizeButton.setAttribute(
        "title",
        "Minimize"
      );

    }


    setTimeout(
      () => {

        input.focus();

      },
      100
    );

  }


  // ======================================================
  // MINIMIZE
  // ======================================================

  if (minimizeButton) {

    minimizeButton.addEventListener(
      "click",
      (event) => {

        event.preventDefault();

        event.stopPropagation();


        const minimized =
          chatPanel.classList.contains(
            "is-minimized"
          );


        if (minimized) {

          restoreChat();

          return;

        }


        const rect =
          chatPanel.getBoundingClientRect();


        const savedLeft =
          rect.left;


        const savedBottom =
          window.innerHeight -
          rect.bottom;


        chatPanel.style.left =
          `${savedLeft}px`;


        chatPanel.style.right =
          "auto";


        chatPanel.style.bottom =
          `${savedBottom}px`;


        chatPanel.style.top =
          "auto";


        chatPanel.classList.add(
          "is-minimized"
        );


        minimizeButton.textContent =
          "□";


        minimizeButton.setAttribute(
          "aria-label",
          "Restore chat"
        );


        minimizeButton.setAttribute(
          "title",
          "Restore"
        );

      }
    );

  }


  // ======================================================
  // CLOSE
  // ======================================================

  if (closeButton) {

    closeButton.addEventListener(
      "click",
      (event) => {

        event.preventDefault();

        event.stopPropagation();

        closeChat();

      }
    );

  }


  // ======================================================
  // HEADER RESTORE
  // ======================================================

  const chatHeader =
    chatPanel.querySelector(
      ".chat-header"
    );


  if (chatHeader) {

    chatHeader.addEventListener(
      "click",
      (event) => {

        if (
          !chatPanel.classList.contains(
            "is-minimized"
          )
        ) {

          return;

        }


        if (
          event.target.closest("button")
        ) {

          return;

        }


        restoreChat();

      }
    );

  }


  // ======================================================
  // DRAG CHAT PANEL
  // ======================================================

  if (chatHeader) {

    let isDragging =
      false;


    let startX =
      0;

    let startY =
      0;

    let startLeft =
      0;

    let startTop =
      0;


    chatHeader.style.cursor =
      "grab";


    chatHeader.addEventListener(
      "mousedown",
      (event) => {

        if (
          event.target.closest("button")
        ) {

          return;

        }


        isDragging =
          true;


        chatHeader.style.cursor =
          "grabbing";


        const rect =
          chatPanel.getBoundingClientRect();


        startX =
          event.clientX;


        startY =
          event.clientY;


        startLeft =
          rect.left;


        startTop =
          rect.top;


        chatPanel.style.right =
          "auto";


        chatPanel.style.bottom =
          "auto";


        chatPanel.style.left =
          `${startLeft}px`;


        chatPanel.style.top =
          `${startTop}px`;


        document.body.style.userSelect =
          "none";

      }
    );


    document.addEventListener(
      "mousemove",
      (event) => {

        if (!isDragging) {

          return;

        }


        const deltaX =
          event.clientX -
          startX;


        const deltaY =
          event.clientY -
          startY;


        const maxLeft =
          window.innerWidth -
          chatPanel.offsetWidth;


        const maxTop =
          window.innerHeight -
          chatPanel.offsetHeight;


        let newLeft =
          startLeft +
          deltaX;


        let newTop =
          startTop +
          deltaY;


        newLeft =
          Math.max(
            0,
            Math.min(
              newLeft,
              maxLeft
            )
          );


        newTop =
          Math.max(
            0,
            Math.min(
              newTop,
              maxTop
            )
          );


        chatPanel.style.left =
          `${newLeft}px`;


        chatPanel.style.top =
          `${newTop}px`;

      }
    );


    document.addEventListener(
      "mouseup",
      () => {

        if (!isDragging) {

          return;

        }


        isDragging =
          false;


        chatHeader.style.cursor =
          "grab";


        document.body.style.userSelect =
          "";

      }
    );

  }


  // ======================================================
  // DRAG FLOATING BUTTON
  // ======================================================

  if (chatToggle) {

    let draggingToggle =
      false;


    let toggleStartX =
      0;

    let toggleStartY =
      0;

    let toggleLeft =
      0;

    let toggleTop =
      0;


    chatToggle.style.cursor =
      "grab";


    chatToggle.addEventListener(
      "mousedown",
      (event) => {

        draggingToggle =
          true;


        toggleWasDragged =
          false;


        chatToggle.style.cursor =
          "grabbing";


        const rect =
          chatToggle.getBoundingClientRect();


        toggleStartX =
          event.clientX;


        toggleStartY =
          event.clientY;


        toggleLeft =
          rect.left;


        toggleTop =
          rect.top;


        chatToggle.style.right =
          "auto";


        chatToggle.style.bottom =
          "auto";


        chatToggle.style.left =
          `${toggleLeft}px`;


        chatToggle.style.top =
          `${toggleTop}px`;


        document.body.style.userSelect =
          "none";

      }
    );


    document.addEventListener(
      "mousemove",
      (event) => {

        if (!draggingToggle) {

          return;

        }


        const deltaX =
          event.clientX -
          toggleStartX;


        const deltaY =
          event.clientY -
          toggleStartY;


        if (
          Math.abs(deltaX) > 5 ||
          Math.abs(deltaY) > 5
        ) {

          toggleWasDragged =
            true;

        }


        const maxLeft =
          window.innerWidth -
          chatToggle.offsetWidth;


        const maxTop =
          window.innerHeight -
          chatToggle.offsetHeight;


        let newLeft =
          toggleLeft +
          deltaX;


        let newTop =
          toggleTop +
          deltaY;


        newLeft =
          Math.max(
            0,
            Math.min(
              newLeft,
              maxLeft
            )
          );


        newTop =
          Math.max(
            0,
            Math.min(
              newTop,
              maxTop
            )
          );


        chatToggle.style.left =
          `${newLeft}px`;


        chatToggle.style.top =
          `${newTop}px`;

      }
    );


    document.addEventListener(
      "mouseup",
      () => {

        if (!draggingToggle) {

          return;

        }


        draggingToggle =
          false;


        chatToggle.style.cursor =
          "grab";


        document.body.style.userSelect =
          "";

      }
    );

  }


  // ======================================================
  // CLEAR CHAT WINDOW
  // ======================================================

  function clearChatWindow() {

    if (chatWindow) {

      chatWindow
        .querySelectorAll(".message")
        .forEach(
          (message) => {

            message.remove();

          }
        );

    }


    if (welcomeScreen) {

      welcomeScreen.style.display =
        "flex";

    }


    if (typingIndicator) {

      typingIndicator.style.display =
        "none";

    }

  }


  // ======================================================
  // RENDER CONVERSATION
  // ======================================================

  function renderConversation(
    conversation
  ) {

    clearChatWindow();


    if (
      !conversation ||
      !Array.isArray(
        conversation.messages
      )
    ) {

      return;

    }


    const messages =
      conversation.messages;


    if (!messages.length) {

      return;

    }


    if (welcomeScreen) {

      welcomeScreen.style.display =
        "none";

    }


    messages.forEach(
      (message) => {

        if (
          !message ||
          !message.content
        ) {

          return;

        }


        if (
          typeof ui !== "undefined"
        ) {

          ui.addMessage(
            message.content,
            message.role === "user"
              ? "user"
              : "bot"
          );

        }

      }
    );

  }


  // ======================================================
  // DELETE CONVERSATION
  // ======================================================

  async function deletePreviousConversation(
    conversationId,
    historyItem
  ) {

    if (!conversationId) {

      return;

    }


    const confirmed =
      window.confirm(
        "Delete this previous chat?\n\nThis action cannot be undone."
      );


    if (!confirmed) {

      return;

    }


    if (
      historyItem?.dataset.deleting ===
      "true"
    ) {

      return;

    }


    if (historyItem) {

      historyItem.dataset.deleting =
        "true";

    }


    try {

      await api.deleteConversation(
        conversationId
      );


      // ----------------------------------------------
      // Remove from history immediately
      // ----------------------------------------------

      if (historyItem) {

        historyItem.remove();

      }


      // ----------------------------------------------
      // If the deleted chat is currently open
      // ----------------------------------------------

      if (
        currentConversationId ===
        conversationId
      ) {

        setConversationId(null);

        clearChatWindow();

        input.value = "";

      }


      // ----------------------------------------------
      // Refresh history
      // ----------------------------------------------

      await loadChatHistory();


    } catch (error) {

      console.error(
        "Could not delete conversation:",
        error
      );


      if (historyItem) {

        historyItem.dataset.deleting =
          "false";

      }


      alert(
        error?.message ||
        "Could not delete this conversation."
      );

    }

  }


  // ======================================================
  // LOAD HISTORY
  // ======================================================

  async function loadChatHistory() {

    if (!chatHistoryList) {

      return;

    }


    chatHistoryList.innerHTML =
      "";


    if (!isAuthenticated()) {

      const emptyMessage =
        document.createElement("p");


      emptyMessage.className =
        "chat-history-empty";


      emptyMessage.textContent =
        "Please login to view previous chats.";


      chatHistoryList.appendChild(
        emptyMessage
      );


      return;

    }


    try {

      const data =
        await api.getChatHistory();


      const conversations =
        Array.isArray(
          data?.conversations
        )
          ? data.conversations
          : [];


      if (!conversations.length) {

        const emptyMessage =
          document.createElement("p");


        emptyMessage.className =
          "chat-history-empty";


        emptyMessage.textContent =
          "No previous chats";


        chatHistoryList.appendChild(
          emptyMessage
        );


        return;

      }


      conversations.forEach(
        (conversation) => {

          // ------------------------------------------
          // HISTORY ITEM WRAPPER
          // ------------------------------------------

          const historyItem =
            document.createElement("div");


          historyItem.className =
            "chat-history-row";


          historyItem.style.display =
            "flex";


          historyItem.style.alignItems =
            "center";


          historyItem.style.gap =
            "6px";


          historyItem.style.width =
            "100%";


          // ------------------------------------------
          // OPEN CHAT BUTTON
          // ------------------------------------------

          const button =
            document.createElement("button");


          button.type =
            "button";


          button.className =
            "chat-history-item";


          button.dataset.conversationId =
            conversation.conversation_id ||
            "";


          button.style.flex =
            "1";


          button.style.minWidth =
            "0";


          const messages =
            Array.isArray(
              conversation.messages
            )
              ? conversation.messages
              : [];


          const firstUserMessage =
            messages.find(
              (message) =>
                message?.role === "user"
            );


          button.textContent =
            firstUserMessage?.content ||
            "Previous conversation";


          button.title =
            firstUserMessage?.content ||
            "Previous conversation";


          // ------------------------------------------
          // DELETE BUTTON
          // ------------------------------------------

          const deleteButton =
            document.createElement("button");


          deleteButton.type =
            "button";


          deleteButton.className =
            "chat-history-delete";


          deleteButton.dataset.conversationId =
            conversation.conversation_id ||
            "";


          deleteButton.innerHTML =
            "🗑";


          deleteButton.title =
            "Delete conversation";


          deleteButton.setAttribute(
            "aria-label",
            "Delete conversation"
          );


          deleteButton.style.flex =
            "0 0 auto";


          deleteButton.style.width =
            "36px";


          deleteButton.style.height =
            "36px";


          deleteButton.style.display =
            "flex";


          deleteButton.style.alignItems =
            "center";


          deleteButton.style.justifyContent =
            "center";


          deleteButton.style.border =
            "0";


          deleteButton.style.borderRadius =
            "8px";


          deleteButton.style.cursor =
            "pointer";


          deleteButton.style.background =
            "transparent";


          deleteButton.style.fontSize =
            "15px";


          // ------------------------------------------
          // DELETE CLICK
          // ------------------------------------------

          deleteButton.addEventListener(
            "click",
            async (event) => {

              event.preventDefault();

              event.stopPropagation();


              await deletePreviousConversation(
                deleteButton.dataset.conversationId,
                historyItem
              );

            }
          );


          // ------------------------------------------
          // OPEN CHAT CLICK
          // ------------------------------------------

          button.addEventListener(
            "click",
            async () => {

              const conversationId =
                button.dataset.conversationId;


              if (!conversationId) {

                return;

              }


              try {

                const selectedConversation =
                  await api.getConversation(
                    conversationId
                  );


                setConversationId(
                  conversationId
                );


                renderConversation(
                  selectedConversation
                );


                openChat();

              } catch (error) {

                console.error(
                  "Could not load conversation:",
                  error
                );

              }

            }
          );


          historyItem.appendChild(
            button
          );


          historyItem.appendChild(
            deleteButton
          );


          chatHistoryList.appendChild(
            historyItem
          );

        }
      );

    } catch (error) {

      console.error(
        "Could not load chat history:",
        error
      );


      const emptyMessage =
        document.createElement("p");


      emptyMessage.className =
        "chat-history-empty";


      emptyMessage.textContent =
        "Unable to load previous chats.";


      chatHistoryList.appendChild(
        emptyMessage
      );

    }

  }


  // ======================================================
  // LOAD CURRENT CONVERSATION
  // ======================================================

  async function loadCurrentConversation() {

    if (!currentConversationId) {

      return;

    }


    if (!isAuthenticated()) {

      setConversationId(null);

      return;

    }


    try {

      const conversation =
        await api.getConversation(
          currentConversationId
        );


      renderConversation(
        conversation
      );

    } catch (error) {

      console.warn(
        "Current conversation could not be loaded:",
        error
      );


      if (
        error.message ===
        "Conversation not found"
      ) {

        setConversationId(null);

        clearChatWindow();

      }

    }

  }


  // ======================================================
  // NEW CHAT
  // ======================================================

  if (newChatButton) {

    newChatButton.addEventListener(
      "click",
      async () => {

        if (
          newChatButton.disabled
        ) {

          return;

        }


        newChatButton.disabled =
          true;


        try {

          clearChatWindow();


          input.value =
            "";


          setConversationId(
            null
          );


          if (sendButton) {

            sendButton.disabled =
              false;


            sendButton.textContent =
              "Send";

          }


          if (isAuthenticated()) {

            try {

              const result =
                await api.resetChat();


              if (
                result?.conversation_id
              ) {

                setConversationId(
                  result.conversation_id
                );

              }

            } catch (resetError) {

              console.warn(
                "Could not reset chat:",
                resetError
              );


              setConversationId(
                null
              );

            }

          }


          await loadChatHistory();


          input.focus();

        } finally {

          newChatButton.disabled =
            false;

        }

      }
    );

  }


  // ======================================================
  // UPLOAD
  // ======================================================

  const allowedExtensions = [

    ".pdf",

    ".doc",

    ".docx",

    ".txt"

  ];


  function getFileExtension(
    filename
  ) {

    const lastDot =
      filename.lastIndexOf(".");


    if (lastDot === -1) {

      return "";

    }


    return filename
      .slice(lastDot)
      .toLowerCase();

  }


  function setUploadStatus(
    message,
    type = ""
  ) {

    if (!uploadStatus) {

      return;

    }


    uploadStatus.textContent =
      message || "";


    uploadStatus.className =
      "upload-status";


    if (type) {

      uploadStatus.classList.add(
        type
      );

    }

  }


  // ======================================================
  // GET CLIENT ID FROM JWT
  // ======================================================

  function getClientIdFromToken() {

    const token =
      getAccessToken();


    if (!token) {

      throw new Error(
        "Not authenticated"
      );

    }


    try {

      const parts =
        token.split(".");


      if (
        parts.length !== 3
      ) {

        throw new Error(
          "Invalid JWT"
        );

      }


      const base64Url =
        parts[1];


      const base64 =
        base64Url
          .replace(/-/g, "+")
          .replace(/_/g, "/");


      const padded =
        base64 +
        "=".repeat(
          (4 -
            (base64.length % 4)) %
          4
        );


      const payload =
        JSON.parse(
          atob(padded)
        );


      console.log(
        "JWT PAYLOAD:",
        payload
      );


      const clientId =
        payload?.client_id ||
        payload?.clientId ||
        payload?.client?.client_id;


      if (!clientId) {

        throw new Error(
          "Client ID not found in authentication token."
        );

      }


      return String(
        clientId
      ).trim();

    } catch (error) {

      console.error(
        "Could not extract client ID from JWT:",
        error
      );


      throw new Error(
        "Could not determine your client ID."
      );

    }

  }


  // ======================================================
  // UPLOAD DOCUMENT
  // ======================================================

  async function uploadSelectedDocument(
    file
  ) {

    if (!file) {

      return;

    }


    if (!isAuthenticated()) {

      setUploadStatus(
        "Please login before uploading a document.",
        "error"
      );


      return;

    }


    const extension =
      getFileExtension(
        file.name
      );


    if (
      !allowedExtensions.includes(
        extension
      )
    ) {

      setUploadStatus(
        "Unsupported file type. Please upload PDF, DOC, DOCX or TXT.",
        "error"
      );


      return;

    }


    chatPanel.classList.add(
      "is-open"
    );


    chatPanel.classList.remove(
      "is-minimized"
    );


    if (chatToggle) {

      chatToggle.textContent =
        "✕";


      chatToggle.setAttribute(
        "aria-label",
        "Close chat"
      );

    }


    if (uploadButton) {

      uploadButton.disabled =
        true;

    }


    setUploadStatus(
      `Uploading ${file.name}...`,
      "loading"
    );


    try {

      console.log(
        "========================================"
      );


      console.log(
        "DOCUMENT UPLOAD START"
      );


      console.log(
        "FILE:",
        file.name
      );


      console.log(
        "TYPE:",
        file.type
      );


      console.log(
        "SIZE:",
        file.size
      );


      console.log(
        "========================================"
      );


      const clientId =
        getClientIdFromToken();


      console.log(
        "UPLOAD CLIENT ID:",
        clientId
      );


      const result =
        await api.uploadDocument(
          file,
          clientId
        );


      console.log(
        "DOCUMENT UPLOAD SUCCESS:",
        result
      );


      setUploadStatus(
        `✅ ${file.name} uploaded successfully. You can now ask questions about it.`,
        "success"
      );


      chatPanel.classList.add(
        "is-open"
      );


      chatPanel.classList.remove(
        "is-minimized"
      );


      if (chatToggle) {

        chatToggle.textContent =
          "✕";


        chatToggle.setAttribute(
          "aria-label",
          "Close chat"
        );

      }

    } catch (error) {

      console.error(
        "DOCUMENT UPLOAD ERROR:",
        error
      );


      setUploadStatus(
        error?.message ||
        "Document upload failed.",
        "error"
      );


      chatPanel.classList.add(
        "is-open"
      );


      chatPanel.classList.remove(
        "is-minimized"
      );


      if (chatToggle) {

        chatToggle.textContent =
          "✕";


        chatToggle.setAttribute(
          "aria-label",
          "Close chat"
        );

      }

    } finally {

      if (uploadButton) {

        uploadButton.disabled =
          false;

      }


      if (documentInput) {

        documentInput.value =
          "";

      }

    }

  }


  // ======================================================
  // FILE PICKER STATE
  // ======================================================

  let filePickerWasOpened =
    false;


  let chatWasOpenBeforePicker =
    false;


  // ======================================================
  // UPLOAD BUTTON
  // ======================================================

  if (
    uploadButton &&
    documentInput
  ) {

    uploadButton.addEventListener(
      "click",
      (event) => {

        event.preventDefault();

        event.stopPropagation();


        if (
          uploadButton.disabled
        ) {

          return;

        }


        chatWasOpenBeforePicker =
          chatPanel.classList.contains(
            "is-open"
          );


        filePickerWasOpened =
          true;


        console.log(
          "Opening document picker..."
        );


        documentInput.click();

      }
    );


    documentInput.addEventListener(
      "change",
      async () => {

        console.log(
          "FILE INPUT CHANGE FIRED"
        );


        const file =
          documentInput.files?.[0];


        console.log(
          "SELECTED FILE:",
          file
        );


        if (
          chatWasOpenBeforePicker
        ) {

          chatPanel.classList.add(
            "is-open"
          );


          chatPanel.classList.remove(
            "is-minimized"
          );


          if (chatToggle) {

            chatToggle.textContent =
              "✕";


            chatToggle.setAttribute(
              "aria-label",
              "Close chat"
            );

          }

        }


        filePickerWasOpened =
          false;


        if (!file) {

          console.log(
            "No file selected."
          );


          return;

        }


        await uploadSelectedDocument(
          file
        );

      }
    );


    window.addEventListener(
      "focus",
      () => {

        if (
          !filePickerWasOpened
        ) {

          return;

        }


        if (
          !chatWasOpenBeforePicker
        ) {

          return;

        }


        setTimeout(
          () => {

            chatPanel.classList.add(
              "is-open"
            );


            chatPanel.classList.remove(
              "is-minimized"
            );


            if (chatToggle) {

              chatToggle.textContent =
                "✕";


              chatToggle.setAttribute(
                "aria-label",
                "Close chat"
              );

            }

          },
          100
        );

      }
    );

  }


  // ======================================================
  // SEND MESSAGE
  // ======================================================

  form.addEventListener(
    "submit",
    async (event) => {

      event.preventDefault();


      const userMessage =
        input.value.trim();


      if (!userMessage) {

        return;

      }


      if (!isAuthenticated()) {

        console.error(
          "Cannot send message: user is not authenticated."
        );


        if (
          typeof ui !== "undefined"
        ) {

          ui.addMessage(
            "Please login before using the chatbot.",
            "bot"
          );

        }


        return;

      }


      if (welcomeScreen) {

        welcomeScreen.style.display =
          "none";

      }


      if (sendButton) {

        sendButton.disabled =
          true;


        sendButton.textContent =
          "...";

      }


      if (
        typeof ui !== "undefined"
      ) {

        ui.addMessage(
          userMessage,
          "user"
        );

      }


      input.value =
        "";


      if (typingIndicator) {

        typingIndicator.style.display =
          "flex";

      }


      try {

        console.log(
          "SENDING AUTHENTICATED CHAT"
        );


        console.log(
          "CONVERSATION ID:",
          currentConversationId
        );


        const result =
          await api.sendMessage({

            message:
              userMessage,

            conversation_id:
              currentConversationId

          });


        console.log(
          "CHAT RESPONSE:",
          result
        );


        if (
          result &&
          result.conversation_id
        ) {

          setConversationId(
            result.conversation_id
          );

        }


        if (
          typeof ui !== "undefined"
        ) {

          ui.addMessage(
            result?.response ||
            result?.message ||
            "No response available.",
            "bot"
          );

        }


        await loadChatHistory();

      } catch (error) {

        console.error(
          "Authenticated chat error:",
          error
        );


        if (
          typeof ui !== "undefined"
        ) {

          ui.addMessage(
            error.message ||
            "Sorry, I could not connect to the chatbot server.",
            "bot"
          );

        }

      } finally {

        if (typingIndicator) {

          typingIndicator.style.display =
            "none";

        }


        if (sendButton) {

          sendButton.disabled =
            false;


          sendButton.textContent =
            "Send";

        }


        input.focus();

      }

    }
  );


  // ======================================================
  // ENTER TO SEND
  // ======================================================

  input.addEventListener(
    "keydown",
    (event) => {

      if (
        event.key === "Enter" &&
        !event.shiftKey
      ) {

        event.preventDefault();


        form.requestSubmit();

      }

    }
  );


  // ======================================================
  // SUGGESTIONS
  // ======================================================

  suggestions.forEach(
    (suggestion) => {

      suggestion.addEventListener(
        "click",
        () => {

          const message =
            suggestion.dataset.message;


          if (!message) {

            return;

          }


          input.value =
            message;


          form.requestSubmit();

        }
      );

    }
  );


  // ======================================================
  // INITIALIZE
  // ======================================================

  async function initializeChatbot() {

    console.log(
      "========================================"
    );


    console.log(
      "INITIALIZING AI CHATBOT PLATFORM"
    );


    console.log(
      "AUTHENTICATED:",
      isAuthenticated()
    );


    console.log(
      "CONVERSATION ID:",
      currentConversationId
    );


    console.log(
      "========================================"
    );


    await loadChatHistory();


    if (currentConversationId) {

      await loadCurrentConversation();

    }

  }


  initializeChatbot();

});