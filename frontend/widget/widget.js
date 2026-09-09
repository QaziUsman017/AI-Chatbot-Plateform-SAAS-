(() => {
  "use strict";

  const params = new URLSearchParams(window.location.search);

  const IS_PREVIEW =
    params.get("preview") === "1" ||
    params.get("preview") === "true";

  const CLIENT_ID = String(
    window.CLIENT_ID ||
    params.get("client_id") ||
    "client_001"
  ).trim();

  const API_BASE = String(
    window.WIDGET_API_BASE ||
    window.API_BASE_URL ||
    window.location.origin
  ).replace(/\/+$/, "");

  const chatPanel = document.getElementById("chat-panel");
  const chatToggle = document.getElementById("chat-toggle");
  const chatHeader = document.getElementById("chat-header");
  const closeButton = document.getElementById("close-button");
  const minimizeButton = document.getElementById("minimize-button");
  const newChatButton = document.getElementById("new-chat-button");
  const chatForm = document.getElementById("chat-form");
  const messageInput = document.getElementById("message-input");
  const sendButton = document.getElementById("send-button");
  const chatWindow = document.getElementById("chat-window");
  const typingIndicator = document.getElementById("typing-indicator");
  const assistantAvatar = document.getElementById("assistant-avatar");
  const welcomeIcon = document.getElementById("welcome-icon");
  const headerTitle = document.getElementById("header-title");
  const welcomeParagraph = document.querySelector(".welcome-screen p");
  const statusText = document.querySelector(".status-text");

  let isOpen = false;
  let isMinimized = false;
  let isSending = false;

  let config = {};

  /*
   * Tracks whether the dashboard has already sent
   * the latest preview configuration.
   *
   * This is used ONLY in preview mode so the default
   * config never overwrites the dashboard configuration.
   */
  let previewConfigReceived = false;

  let conversationId = null;
  let messages = [];

  const visitorKey =
    `ai_chatbot_visitor_${CLIENT_ID}`;

  const conversationsKey =
    `ai_chatbot_conversations_${CLIENT_ID}`;

  const activeConversationKey =
    `ai_chatbot_active_${CLIENT_ID}`;


  /* =========================================================
     DEFAULT CONFIG
     ========================================================= */

  const DEFAULT_CONFIG = {
    primary_color: "#0ea5e9",
    secondary_color: "#0f172a",
    text_color: "#0f172a",

    bot_name: "AI Assistant",
    logo: "",
    position: "bottom-right",
    welcome_message:
      "Hi! How can I help you today?",

    background_color: "#0b0d0c",
    surface_color: "#111513",
    surface_secondary_color: "#161a18",
    surface_tertiary_color: "#1c211f",

    text_primary_color: "#f5f7f6",
    text_secondary_color: "#d8dedb",
    text_muted_color: "#929b97",
    text_muted_dark_color: "#68716d",

    border_color:
      "rgba(255,255,255,0.08)",

    border_light_color:
      "rgba(255,255,255,0.12)",

    header_background_color: "#111513",
    header_text_color: "#f5f7f6",
    header_secondary_text_color: "#929b97",
    header_button_color: "#929b97",

    header_button_background_color:
      "rgba(255,255,255,0.06)",

    header_button_border_color:
      "rgba(255,255,255,0.08)",

    avatar_background_color: "#10b981",
    avatar_text_color: "#ffffff",

    welcome_icon_background_color:
      "#10b981",

    welcome_icon_text_color:
      "#ffffff",

    status_dot_color: "#22c55e",
    status_text_color: "#929b97",

    user_message_background_color:
      "#242a27",

    user_message_text_color:
      "#f2f5f3",

    user_message_border_color:
      "rgba(255,255,255,0.09)",

    assistant_message_background_color:
      "#1b211f",

    assistant_message_text_color:
      "#e7ece9",

    assistant_message_border_color:
      "rgba(255,255,255,0.10)",

    composer_background_color: "#111513",

    input_background_color: "#161a18",

    input_text_color: "#f5f7f6",

    input_placeholder_color: "#929b97",

    input_border_color:
      "rgba(255,255,255,0.10)",

    input_focus_border_color:
      "#10b981",

    send_button_background_color:
      "#10b981",

    send_button_text_color:
      "#ffffff",

    launcher_background_color:
      "#10b981",

    launcher_icon_color:
      "#ffffff",

    typing_background_color:
      "#161a18",

    typing_dot_color:
      "#929b97",

    code_background_color:
      "#0b0e0d",

    code_text_color:
      "#e7ece9",

    danger_color:
      "#ef4444",

    success_color:
      "#22c55e"
  };


  /* =========================================================
     BASIC HELPERS
     ========================================================= */

  function generateId() {
    if (
      window.crypto &&
      typeof window.crypto.randomUUID ===
        "function"
    ) {
      return window.crypto.randomUUID();
    }

    return (
      "id_" +
      Date.now() +
      "_" +
      Math.random()
        .toString(36)
        .substring(2, 12)
    );
  }


  function getVisitorId() {
    let id =
      localStorage.getItem(visitorKey);

    if (!id) {
      id = generateId();

      localStorage.setItem(
        visitorKey,
        id
      );
    }

    return id;
  }


  const visitorId =
    getVisitorId();


  function readJSON(
    key,
    fallback
  ) {
    try {
      const value =
        localStorage.getItem(key);

      if (!value) {
        return fallback;
      }

      const parsed =
        JSON.parse(value);

      return parsed ?? fallback;
    } catch {
      return fallback;
    }
  }


  function writeJSON(
    key,
    value
  ) {
    try {
      localStorage.setItem(
        key,
        JSON.stringify(value)
      );
    } catch {}
  }


  /* =========================================================
     COLOR HELPERS
     ========================================================= */

  function isValidColor(value) {
    if (!value) {
      return false;
    }

    const color =
      String(value).trim();

    if (!color) {
      return false;
    }

    if (
      typeof CSS !== "undefined" &&
      typeof CSS.supports === "function"
    ) {
      return CSS.supports(
        "color",
        color
      );
    }

    return (
      /^#[0-9a-fA-F]{3,8}$/.test(color) ||
      /^rgba?\(/i.test(color) ||
      /^hsla?\(/i.test(color)
    );
  }


  function setCSSVariable(
    variable,
    value,
    fallback = ""
  ) {
    const finalValue =
      isValidColor(value)
        ? String(value).trim()
        : fallback;

    if (!finalValue) {
      return;
    }

    document.documentElement.style.setProperty(
      variable,
      finalValue
    );
  }


  function colorToRgba(
    color,
    alpha
  ) {
    const value =
      String(color || "").trim();

    if (
      /^rgba?\(/i.test(value)
    ) {
      const match =
        value.match(
          /rgba?\(\s*([^)]*)\)/i
        );

      if (match) {
        const parts =
          match[1]
            .split(",")
            .map(
              item =>
                item.trim()
            );

        if (
          parts.length >= 3
        ) {
          return `rgba(${parts[0]}, ${parts[1]}, ${parts[2]}, ${alpha})`;
        }
      }
    }

    if (
      /^#/i.test(value)
    ) {
      let hex =
        value.substring(1);

      if (
        hex.length === 3
      ) {
        hex =
          hex
            .split("")
            .map(
              char =>
                char + char
            )
            .join("");
      }

      if (
        hex.length >= 6
      ) {
        const r =
          parseInt(
            hex.substring(0, 2),
            16
          );

        const g =
          parseInt(
            hex.substring(2, 4),
            16
          );

        const b =
          parseInt(
            hex.substring(4, 6),
            16
          );

        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
      }
    }

    return `rgba(16,185,129,${alpha})`;
  }


  function darkenColor(color) {
    let value =
      String(color || "").trim();

    if (!value.startsWith("#")) {
      return "#059669";
    }

    value =
      value.substring(1);

    if (
      value.length === 3
    ) {
      value =
        value
          .split("")
          .map(
            char =>
              char + char
          )
          .join("");
    }

    if (
      value.length !== 6
    ) {
      return "#059669";
    }

    const r =
      Math.max(
        0,
        parseInt(
          value.substring(0, 2),
          16
        ) - 25
      );

    const g =
      Math.max(
        0,
        parseInt(
          value.substring(2, 4),
          16
        ) - 25
      );

    const b =
      Math.max(
        0,
        parseInt(
          value.substring(4, 6),
          16
        ) - 25
      );

    return (
      "#" +
      [r, g, b]
        .map(
          number =>
            number
              .toString(16)
              .padStart(2, "0")
        )
        .join("")
    );
  }


  /* =========================================================
     CONFIG LOAD
     ========================================================= */

  async function loadWidgetConfig() {
    if (IS_PREVIEW) {
      /*
       * In preview mode, the dashboard is the source of truth.
       *
       * Do not overwrite a configuration that has already
       * arrived through postMessage from the dashboard.
       */
      if (!previewConfigReceived) {
        config = {
          ...DEFAULT_CONFIG,
          ...config
        };

        applyConfig();
      }

      return;
    }

    try {
      const response =
        await fetch(
          `${API_BASE}/widget/config?client_id=${encodeURIComponent(
            CLIENT_ID
          )}`,
          {
            method: "GET",
            cache: "no-store",
            headers: {
              Accept:
                "application/json"
            }
          }
        );

      if (!response.ok) {
        throw new Error(
          `Config request failed with status ${response.status}`
        );
      }

      const data =
        await response.json();

      config = {
        ...DEFAULT_CONFIG,
        ...(data?.config || {})
      };

      applyConfig();

    } catch (error) {
      console.warn(
        "[Widget] Config load failed. Using defaults:",
        error
      );

      config = {
        ...DEFAULT_CONFIG
      };

      applyConfig();
    }
  }


  function getBotName() {
    return (
      String(
        config.bot_name ||
        config.agent_name ||
        "AI Assistant"
      ).trim() ||
      "AI Assistant"
    );
  }


  /* =========================================================
     APPLY CONFIG
     ========================================================= */

  function applyConfig() {
    config = {
      ...DEFAULT_CONFIG,
      ...(config || {})
    };

    const root =
      document.documentElement;

    const primary =
      isValidColor(
        config.primary_color
      )
        ? config.primary_color
        : DEFAULT_CONFIG.primary_color;

    const botName =
      getBotName();

    const logo =
      String(
        config.logo || ""
      ).trim();


    /* -------------------------------------------------------
       Core
       ------------------------------------------------------- */

    setCSSVariable(
      "--primary",
      primary
    );

    setCSSVariable(
      "--secondary",
      config.secondary_color,
      DEFAULT_CONFIG.secondary_color
    );

    setCSSVariable(
      "--accent",
      primary
    );

    setCSSVariable(
      "--accent-dark",
      darkenColor(primary)
    );

    root.style.setProperty(
      "--accent-soft",
      colorToRgba(
        primary,
        0.12
      )
    );

    root.style.setProperty(
      "--accent-border",
      colorToRgba(
        primary,
        0.28
      )
    );


    /* -------------------------------------------------------
       Backgrounds
       ------------------------------------------------------- */

    setCSSVariable(
      "--bg",
      config.background_color
    );

    setCSSVariable(
      "--surface",
      config.surface_color
    );

    setCSSVariable(
      "--surface-2",
      config.surface_secondary_color
    );

    setCSSVariable(
      "--surface-3",
      config.surface_tertiary_color
    );


    /* -------------------------------------------------------
       Text
       ------------------------------------------------------- */

    setCSSVariable(
      "--text",
      config.text_primary_color ||
        config.text_color
    );

    setCSSVariable(
      "--text-primary",
      config.text_primary_color ||
        config.text_color
    );

    setCSSVariable(
      "--text-secondary",
      config.text_secondary_color
    );

    setCSSVariable(
      "--muted",
      config.text_muted_color
    );

    setCSSVariable(
      "--text-muted",
      config.text_muted_color
    );

    setCSSVariable(
      "--muted-dark",
      config.text_muted_dark_color
    );


    /* -------------------------------------------------------
       Borders
       ------------------------------------------------------- */

    setCSSVariable(
      "--border",
      config.border_color
    );

    setCSSVariable(
      "--border-light",
      config.border_light_color
    );


    /* -------------------------------------------------------
       Header
       ------------------------------------------------------- */

    setCSSVariable(
      "--header-background",
      config.header_background_color
    );

    setCSSVariable(
      "--header-text",
      config.header_text_color
    );

    setCSSVariable(
      "--header-secondary-text",
      config.header_secondary_text_color
    );

    setCSSVariable(
      "--header-button",
      config.header_button_color
    );

    setCSSVariable(
      "--header-button-background",
      config.header_button_background_color
    );

    setCSSVariable(
      "--header-button-border",
      config.header_button_border_color
    );


    /* -------------------------------------------------------
       Avatar
       ------------------------------------------------------- */

    setCSSVariable(
      "--avatar-background",
      config.avatar_background_color
    );

    setCSSVariable(
      "--avatar-text",
      config.avatar_text_color
    );


    /* -------------------------------------------------------
       Welcome icon
       ------------------------------------------------------- */

    setCSSVariable(
      "--welcome-icon-background",
      config.welcome_icon_background_color
    );

    setCSSVariable(
      "--welcome-icon-text",
      config.welcome_icon_text_color
    );


    /* -------------------------------------------------------
       Status
       ------------------------------------------------------- */

    setCSSVariable(
      "--status-dot",
      config.status_dot_color
    );

    setCSSVariable(
      "--status-text",
      config.status_text_color
    );


    /* -------------------------------------------------------
       User message
       ------------------------------------------------------- */

    setCSSVariable(
      "--user-message-background",
      config.user_message_background_color
    );

    setCSSVariable(
      "--user-message-text",
      config.user_message_text_color
    );

    setCSSVariable(
      "--user-message-border",
      config.user_message_border_color
    );


    /* -------------------------------------------------------
       Assistant message
       ------------------------------------------------------- */

    setCSSVariable(
      "--assistant-message-background",
      config.assistant_message_background_color
    );

    setCSSVariable(
      "--assistant-message-text",
      config.assistant_message_text_color
    );

    setCSSVariable(
      "--assistant-message-border",
      config.assistant_message_border_color
    );


    /* -------------------------------------------------------
       Composer
       ------------------------------------------------------- */

    setCSSVariable(
      "--composer-background",
      config.composer_background_color
    );

    setCSSVariable(
      "--input-background",
      config.input_background_color
    );

    setCSSVariable(
      "--input-text",
      config.input_text_color
    );

    setCSSVariable(
      "--input-placeholder",
      config.input_placeholder_color
    );

    setCSSVariable(
      "--input-border",
      config.input_border_color
    );

    setCSSVariable(
      "--input-focus-border",
      config.input_focus_border_color
    );


    /* -------------------------------------------------------
       Buttons
       ------------------------------------------------------- */

    setCSSVariable(
      "--send-button-background",
      config.send_button_background_color
    );

    setCSSVariable(
      "--send-button-text",
      config.send_button_text_color
    );

    setCSSVariable(
      "--launcher-background",
      config.launcher_background_color
    );

    setCSSVariable(
      "--launcher-icon",
      config.launcher_icon_color
    );


    /* -------------------------------------------------------
       Typing
       ------------------------------------------------------- */

    setCSSVariable(
      "--typing-background",
      config.typing_background_color
    );

    setCSSVariable(
      "--typing-dot",
      config.typing_dot_color
    );


    /* -------------------------------------------------------
       Code
       ------------------------------------------------------- */

    setCSSVariable(
      "--code-background",
      config.code_background_color
    );

    setCSSVariable(
      "--code-text",
      config.code_text_color
    );


    /* -------------------------------------------------------
       Utility colors
       ------------------------------------------------------- */

    setCSSVariable(
      "--danger",
      config.danger_color
    );

    setCSSVariable(
      "--success",
      config.success_color
    );


    /* -------------------------------------------------------
       Identity
       ------------------------------------------------------- */

    if (headerTitle) {
      headerTitle.textContent =
        botName;
    }

    if (welcomeParagraph) {
      welcomeParagraph.textContent =
        config.welcome_message ||
        DEFAULT_CONFIG.welcome_message;
    }

    if (statusText) {
      statusText.textContent =
        "Online";
    }

    if (chatToggle) {
      chatToggle.setAttribute(
        "aria-label",
        `Open ${botName} chat`
      );

      chatToggle.setAttribute(
        "title",
        `Open ${botName} chat`
      );
    }

    document.title =
      botName;


    /* -------------------------------------------------------
       Logo / avatar
       ------------------------------------------------------- */

    updateIdentityLogo(
      assistantAvatar,
      logo,
      botName
    );

    updateIdentityLogo(
      welcomeIcon,
      logo,
      botName
    );


    /* -------------------------------------------------------
       IMPORTANT:
       Uploaded logo completely replaces the floating launcher.
       No background/border/shadow is shown behind the logo.
       If no logo exists, the original 💬 launcher is restored.
       ------------------------------------------------------- */

    updateLauncherLogo(
      logo,
      botName
    );


    /* -------------------------------------------------------
       Re-render messages so avatar/config changes
       immediately appear.
       ------------------------------------------------------- */

    renderMessages();


    window.__widgetConfig =
      {
        ...config
      };

    window.dispatchEvent(
      new CustomEvent(
        "widget:config-applied",
        {
          detail: {
            ...config
          }
        }
      )
    );
  }


  /* =========================================================
     LAUNCHER LOGO
     ========================================================= */

  function updateLauncherLogo(
    logo,
    botName
  ) {
    if (!chatToggle) {
      return;
    }

    const cleanLogo =
      String(
        logo || ""
      ).trim();

    /*
     * Always clear the existing launcher content first.
     * This prevents an old logo from remaining after
     * the configuration changes or the logo is removed.
     */
    chatToggle.replaceChildren();

    /*
     * No logo:
     * restore the original launcher appearance and 💬 icon.
     */
    if (!cleanLogo) {
      chatToggle.classList.remove(
        "has-logo"
      );

      chatToggle.textContent =
        "💬";

      return;
    }

    /*
     * Logo exists:
     * enable logo mode.
     *
     * CSS removes:
     * - launcher background
     * - border
     * - shadow
     *
     * The image itself becomes the visible launcher.
     */
    chatToggle.classList.add(
      "has-logo"
    );

    const image =
      document.createElement(
        "img"
      );

    image.src =
      cleanLogo;

    image.alt =
      `${botName} logo`;

    image.draggable =
      false;

    /*
     * If the logo URL/data is invalid,
     * safely restore the original 💬 launcher.
     */
    image.onerror = () => {
      chatToggle.classList.remove(
        "has-logo"
      );

      chatToggle.replaceChildren();

      chatToggle.textContent =
        "💬";
    };

    chatToggle.appendChild(
      image
    );
  }


  function updateIdentityLogo(
    element,
    logo,
    botName
  ) {
    if (!element) {
      return;
    }

    element.replaceChildren();

    if (logo) {
      const image =
        document.createElement(
          "img"
        );

      image.src = logo;
      image.alt = botName;

      image.onerror = () => {
        element.replaceChildren();

        element.textContent =
          getInitials(botName);
      };

      element.appendChild(
        image
      );

      return;
    }

    element.textContent =
      getInitials(botName);
  }


  function getInitials(name) {
    const words =
      String(
        name || "AI Assistant"
      )
        .trim()
        .split(/\s+/)
        .filter(Boolean);

    if (!words.length) {
      return "AI";
    }

    if (
      words.length === 1
    ) {
      return words[0]
        .substring(0, 2)
        .toUpperCase();
    }

    return (
      words[0][0] +
      words[1][0]
    ).toUpperCase();
  }


  function escapeHtml(value) {
    return String(value ?? "")
      .replace(
        /&/g,
        "&amp;"
      )
      .replace(
        /</g,
        "&lt;"
      )
      .replace(
        />/g,
        "&gt;"
      )
      .replace(
        /"/g,
        "&quot;"
      )
      .replace(
        /'/g,
        "&#039;"
      );
  }


  function escapeAttribute(value) {
    return escapeHtml(value);
  }


  function formatMessage(text) {
    let value =
      escapeHtml(text);

    value =
      value.replace(
        /```([\s\S]*?)```/g,
        "<pre>$1</pre>"
      );

    value =
      value.replace(
        /`([^`]+)`/g,
        "<code>$1</code>"
      );

    value =
      value.replace(
        /\*\*([^*]+)\*\*/g,
        "<strong>$1</strong>"
      );

    value =
      value.replace(
        /\n/g,
        "<br>"
      );

    return value;
  }


  /* =========================================================
     MINIMIZE
     ========================================================= */

  function updateMinimizeButton() {
    if (!minimizeButton) {
      return;
    }

    if (isMinimized) {
      minimizeButton.innerHTML = `
        <svg
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <rect
            x="5"
            y="5"
            width="14"
            height="14"
            rx="1.5"
          ></rect>
        </svg>
      `;

      minimizeButton.setAttribute(
        "aria-label",
        "Restore chat"
      );

      minimizeButton.title =
        "Restore";
    } else {
      minimizeButton.innerHTML = `
        <span
          class="minus-icon"
          aria-hidden="true"
        >
          −
        </span>
      `;

      minimizeButton.setAttribute(
        "aria-label",
        "Minimize chat"
      );

      minimizeButton.title =
        "Minimize";
    }
  }


  /* =========================================================
     OPEN / CLOSE
     ========================================================= */

  function openChat() {
    if (!chatPanel) {
      return;
    }

    isOpen = true;
    isMinimized = false;

    chatPanel.classList.add(
      "open",
      "is-open"
    );

    chatPanel.classList.remove(
      "is-closed",
      "minimized",
      "is-minimized"
    );

    chatPanel.setAttribute(
      "aria-hidden",
      "false"
    );

    chatPanel.style.visibility =
      "visible";

    chatPanel.style.opacity =
      "1";

    chatPanel.style.pointerEvents =
      "auto";

    document.body.classList.add(
      "chat-open"
    );

    updateMinimizeButton();

    notifyParent(
      "widget:open"
    );

    setTimeout(() => {
      if (
        messageInput &&
        !isMinimized
      ) {
        messageInput.focus();
      }
    }, 150);
  }


  function closeChat() {
    if (!chatPanel) {
      return;
    }

    isOpen = false;
    isMinimized = false;

    chatPanel.classList.remove(
      "open",
      "is-open",
      "minimized",
      "is-minimized"
    );

    chatPanel.classList.add(
      "is-closed"
    );

    chatPanel.setAttribute(
      "aria-hidden",
      "true"
    );

    chatPanel.style.visibility =
      "hidden";

    chatPanel.style.opacity =
      "0";

    chatPanel.style.pointerEvents =
      "none";

    document.body.classList.remove(
      "chat-open"
    );

    updateMinimizeButton();

    notifyParent(
      "widget:close"
    );
  }


  function minimizeChat() {
    if (
      !chatPanel ||
      !isOpen
    ) {
      return;
    }

    isMinimized = true;

    chatPanel.classList.add(
      "open",
      "is-open",
      "minimized",
      "is-minimized"
    );

    chatPanel.classList.remove(
      "is-closed"
    );

    chatPanel.style.visibility =
      "visible";

    chatPanel.style.opacity =
      "1";

    chatPanel.style.pointerEvents =
      "auto";

    document.body.classList.add(
      "chat-open"
    );

    updateMinimizeButton();

    notifyParent(
      "widget:minimize"
    );
  }


  function restoreChat() {
    if (
      !chatPanel ||
      !isOpen
    ) {
      return;
    }

    isMinimized = false;

    chatPanel.classList.add(
      "open",
      "is-open"
    );

    chatPanel.classList.remove(
      "is-closed",
      "minimized",
      "is-minimized"
    );

    chatPanel.style.visibility =
      "visible";

    chatPanel.style.opacity =
      "1";

    chatPanel.style.pointerEvents =
      "auto";

    document.body.classList.add(
      "chat-open"
    );

    updateMinimizeButton();

    notifyParent(
      "widget:restore"
    );

    setTimeout(() => {
      if (messageInput) {
        messageInput.focus();
      }
    }, 100);
  }


  /* =========================================================
     VISITOR
     ========================================================= */

  async function registerVisitor() {
    if (IS_PREVIEW) {
      return;
    }

    try {
      await fetch(
        `${API_BASE}/widget/visit`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body: JSON.stringify({
            visitor_id:
              visitorId,

            client_id:
              CLIENT_ID
          })
        }
      );
    } catch (error) {
      console.warn(
        "[Widget] Visitor registration failed:",
        error
      );
    }
  }


  /* =========================================================
     CONVERSATION STORAGE
     ========================================================= */

  function getConversations() {
    const data =
      readJSON(
        conversationsKey,
        []
      );

    return Array.isArray(data)
      ? data
      : [];
  }


  function saveConversations(
    conversations
  ) {
    writeJSON(
      conversationsKey,
      conversations
    );
  }


  function createConversation(
    title = "New conversation"
  ) {
    const conversation = {
      id: generateId(),

      title:
        title.trim()
          ? makeTitle(title)
          : "New conversation",

      createdAt:
        Date.now(),

      updatedAt:
        Date.now(),

      messages: []
    };

    const conversations =
      getConversations();

    conversations.unshift(
      conversation
    );

    saveConversations(
      conversations
    );

    conversationId =
      conversation.id;

    messages = [];

    localStorage.setItem(
      activeConversationKey,
      conversationId
    );

    return conversation;
  }


  function makeTitle(text) {
    const clean =
      String(text || "")
        .replace(/\s+/g, " ")
        .trim();

    if (!clean) {
      return "New conversation";
    }

    if (
      clean.length <= 30
    ) {
      return clean;
    }

    return (
      clean.substring(0, 30) +
      "..."
    );
  }


  function loadConversation(id) {
    const conversations =
      getConversations();

    const conversation =
      conversations.find(
        item =>
          item.id === id
      );

    if (!conversation) {
      return false;
    }

    conversationId =
      conversation.id;

    messages =
      Array.isArray(
        conversation.messages
      )
        ? conversation.messages
        : [];

    localStorage.setItem(
      activeConversationKey,
      conversationId
    );

    renderMessages();

    return true;
  }


  function saveConversation() {
    if (!conversationId) {
      return;
    }

    const conversations =
      getConversations();

    const index =
      conversations.findIndex(
        item =>
          item.id ===
          conversationId
      );

    if (index === -1) {
      return;
    }

    conversations[index].messages =
      messages;

    conversations[index].updatedAt =
      Date.now();

    const firstUserMessage =
      messages.find(
        item =>
          item.role === "user"
      );

    if (
      firstUserMessage &&
      conversations[index].title ===
        "New conversation"
    ) {
      conversations[index].title =
        makeTitle(
          firstUserMessage.content
        );
    }

    conversations.sort(
      (a, b) =>
        (b.updatedAt || 0) -
        (a.updatedAt || 0)
    );

    saveConversations(
      conversations
    );
  }


  function loadActiveConversation() {
    if (IS_PREVIEW) {
      messages = [];
      conversationId = null;

      renderMessages();

      return;
    }

    const activeId =
      localStorage.getItem(
        activeConversationKey
      );

    if (
      activeId &&
      loadConversation(activeId)
    ) {
      return;
    }

    const conversations =
      getConversations();

    if (conversations.length) {
      loadConversation(
        conversations[0].id
      );

      return;
    }

    createConversation();
  }


  function addMessage(
    role,
    content
  ) {
    messages.push({
      role,

      content:
        String(content || "")
    });

    if (!IS_PREVIEW) {
      saveConversation();
    }

    renderMessages();
  }


  /* =========================================================
     MESSAGE RENDERING
     ========================================================= */

  function renderMessages() {
    if (!chatWindow) {
      return;
    }

    chatWindow.innerHTML =
      "";

    if (!messages.length) {
      const welcome =
        document.createElement(
          "div"
        );

      welcome.className =
        "welcome-screen";

      welcome.id =
        "welcome-screen";

      const icon =
        document.createElement(
          "div"
        );

      icon.className =
        "welcome-icon";

      updateIdentityLogo(
        icon,
        String(config.logo || "").trim(),
        getBotName()
      );

      const heading =
        document.createElement(
          "h2"
        );

      heading.textContent =
        "How can I help you?";

      const paragraph =
        document.createElement(
          "p"
        );

      paragraph.textContent =
        config.welcome_message ||
        DEFAULT_CONFIG.welcome_message;

      welcome.appendChild(
        icon
      );

      welcome.appendChild(
        heading
      );

      welcome.appendChild(
        paragraph
      );

      chatWindow.appendChild(
        welcome
      );

      return;
    }

    messages.forEach(
      message => {
        const role =
          message.role === "user"
            ? "user"
            : "assistant";

        const row =
          document.createElement(
            "div"
          );

        row.className =
          `message ${role}`;

        if (
          role === "assistant"
        ) {
          const miniAvatar =
            document.createElement(
              "div"
            );

          miniAvatar.className =
            "message-avatar";

          updateIdentityLogo(
            miniAvatar,
            String(
              config.logo || ""
            ).trim(),
            getBotName()
          );

          row.appendChild(
            miniAvatar
          );
        }

        const bubble =
          document.createElement(
            "div"
          );

        bubble.className =
          "message-bubble";

        bubble.innerHTML =
          formatMessage(
            message.content
          );

        row.appendChild(
          bubble
        );

        chatWindow.appendChild(
          row
        );
      }
    );

    scrollToBottom();
  }


  /* =========================================================
     NEW CHAT
     ========================================================= */

  function newChat() {
    if (isSending) {
      return;
    }

    if (IS_PREVIEW) {
      messages = [];
      conversationId = null;

      renderMessages();

      if (messageInput) {
        messageInput.value = "";
      }

      return;
    }

    createConversation();

    renderMessages();

    if (messageInput) {
      messageInput.value = "";
      messageInput.focus();
    }

    notifyParent(
      "widget:new-chat"
    );
  }


  /* =========================================================
     SEND MESSAGE
     ========================================================= */

  async function sendMessage(event) {
    if (event) {
      event.preventDefault();
    }

    if (IS_PREVIEW) {
      return;
    }

    if (isSending) {
      return;
    }

    const text =
      messageInput?.value?.trim();

    if (!text) {
      return;
    }

    if (!conversationId) {
      createConversation(text);
    }

    isSending = true;

    if (sendButton) {
      sendButton.disabled =
        true;
    }

    if (messageInput) {
      messageInput.disabled =
        true;
    }

    addMessage(
      "user",
      text
    );

    if (messageInput) {
      messageInput.value =
        "";
    }

    showTyping();

    try {
      const response =
        await fetch(
          `${API_BASE}/widget/chat`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json"
            },

            body: JSON.stringify({
              message: text,

              client_id:
                CLIENT_ID,

              visitor_id:
                visitorId,

              conversation_id:
                conversationId,

              conversation_history:
                messages
            })
          }
        );

      if (!response.ok) {
        let detail =
          `Server error (${response.status})`;

        try {
          const errorData =
            await response.json();

          detail =
            errorData?.detail ||
            errorData?.message ||
            detail;

        } catch {
          try {
            const errorText =
              await response.text();

            if (errorText) {
              detail =
                errorText;
            }
          } catch {}
        }

        throw new Error(
          detail
        );
      }

      const data =
        await response.json();

      if (
        data.conversation_id
      ) {
        conversationId =
          data.conversation_id;

        localStorage.setItem(
          activeConversationKey,
          conversationId
        );
      }

      const answer =
        data.response ||
        data.answer ||
        data.message ||
        "I couldn't generate a response.";

      addMessage(
        "assistant",
        answer
      );

    } catch (error) {
      console.error(
        "[Widget] Chat error:",
        error
      );

      addMessage(
        "assistant",
        `Sorry, something went wrong. ${
          error.message ||
          "Please try again."
        }`
      );

    } finally {
      hideTyping();

      isSending = false;

      if (sendButton) {
        sendButton.disabled =
          false;
      }

      if (messageInput) {
        messageInput.disabled =
          false;

        messageInput.focus();
      }
    }
  }


  /* =========================================================
     TYPING
     ========================================================= */

  function showTyping() {
    if (!typingIndicator) {
      return;
    }

    typingIndicator.classList.add(
      "active"
    );

    scrollToBottom();
  }


  function hideTyping() {
    if (!typingIndicator) {
      return;
    }

    typingIndicator.classList.remove(
      "active"
    );
  }


  function scrollToBottom() {
    requestAnimationFrame(
      () => {
        if (chatWindow) {
          chatWindow.scrollTop =
            chatWindow.scrollHeight;
        }
      }
    );
  }


  /* =========================================================
     PARENT / LOADER MESSAGING
     ========================================================= */

  function notifyParent(
    type,
    data = {}
  ) {
    try {
      window.parent.postMessage(
        {
          source:
            "ai-chatbot-widget",

          type,

          client_id:
            CLIENT_ID,

          ...data
        },

        "*"
      );
    } catch {}
  }


  /* =========================================================
     PREVIEW CONFIG
     ========================================================= */

  function applyPreviewConfig(
    incomingConfig
  ) {
    if (!IS_PREVIEW) {
      return;
    }

    /*
     * The dashboard has now provided the actual
     * configuration for this preview.
     */
    previewConfigReceived = true;

    config = {
      ...DEFAULT_CONFIG,
      ...(incomingConfig || {})
    };

    applyConfig();
  }


  function setupPreviewMessaging() {
    if (!IS_PREVIEW) {
      return;
    }

    window.addEventListener(
      "message",
      event => {
        const data =
          event.data;

        if (!data) {
          return;
        }

        if (
          data.type ===
          "widget:preview-config"
        ) {
          applyPreviewConfig(
            data.config || {}
          );

          return;
        }

        if (
          data.type ===
          "widget:preview-open"
        ) {
          openChat();

          return;
        }

        if (
          data.type ===
          "widget:preview-close"
        ) {
          closeChat();

          return;
        }
      }
    );
  }


  /* =========================================================
     DRAG SYSTEM
     ========================================================= */

  let dragState = null;
  let suppressNextClick = false;


  function isInteractiveElement(
    element
  ) {
    if (!element) {
      return false;
    }

    return Boolean(
      element.closest(
        "button, input, textarea, select, a"
      )
    );
  }


  function setupDrag(
    target,
    options = {}
  ) {
    if (!target) {
      return;
    }

    target.style.cursor =
      "grab";

    target.addEventListener(
      "pointerdown",
      event => {
        if (
          options.excludeControls &&
          isInteractiveElement(
            event.target
          )
        ) {
          return;
        }

        if (
          event.pointerType ===
            "mouse" &&
          event.button !== 0
        ) {
          return;
        }

        dragState = {
          target,

          pointerId:
            event.pointerId,

          startX:
            event.screenX,

          startY:
            event.screenY,

          moved: false
        };

        target.style.cursor =
          "grabbing";

        try {
          target.setPointerCapture(
            event.pointerId
          );
        } catch {}
      },
      {
        passive: false
      }
    );


    target.addEventListener(
      "pointermove",
      event => {
        if (!dragState) {
          return;
        }

        if (
          event.pointerId !==
          dragState.pointerId
        ) {
          return;
        }

        const currentX =
          event.screenX;

        const currentY =
          event.screenY;

        const dx =
          currentX -
          dragState.startX;

        const dy =
          currentY -
          dragState.startY;

        if (
          !dragState.moved &&
          Math.hypot(dx, dy) < 5
        ) {
          return;
        }

        if (
          !dragState.moved
        ) {
          dragState.moved =
            true;

          suppressNextClick =
            true;

          notifyParent(
            "widget:drag-start",
            {
              screenX:
                currentX,

              screenY:
                currentY
            }
          );
        }

        notifyParent(
          "widget:drag-move",
          {
            screenX:
              currentX,

            screenY:
              currentY
          }
        );

        event.preventDefault();
      },
      {
        passive: false
      }
    );


    const finishDrag =
      event => {
        if (!dragState) {
          return;
        }

        if (
          event.pointerId !==
          dragState.pointerId
        ) {
          return;
        }

        const wasDragging =
          dragState.moved;

        if (wasDragging) {
          notifyParent(
            "widget:drag-end",
            {
              screenX:
                event.screenX,

              screenY:
                event.screenY
            }
          );

          setTimeout(() => {
            suppressNextClick =
              false;
          }, 180);
        }

        dragState.target.style.cursor =
          "grab";

        try {
          dragState.target.releasePointerCapture(
            dragState.pointerId
          );
        } catch {}

        dragState = null;
      };


    target.addEventListener(
      "pointerup",
      finishDrag,
      {
        passive: false
      }
    );

    target.addEventListener(
      "pointercancel",
      finishDrag,
      {
        passive: false
      }
    );

    target.addEventListener(
      "pointerleave",
      () => {
        if (
          dragState &&
          dragState.target === target
        ) {
          target.style.cursor =
            "grabbing";
        }
      }
    );
  }


  setupDrag(
    chatToggle
  );

  setupDrag(
    chatHeader,
    {
      excludeControls: true
    }
  );


  /* =========================================================
     FLOATING BUTTON
     ========================================================= */

  if (chatToggle) {
    chatToggle.addEventListener(
      "click",
      event => {
        if (suppressNextClick) {
          event.preventDefault();
          event.stopPropagation();

          return;
        }

        if (isOpen) {
          if (isMinimized) {
            restoreChat();
          } else {
            closeChat();
          }
        } else {
          openChat();
        }
      }
    );
  }


  /* =========================================================
     CLOSE
     ========================================================= */

  if (closeButton) {
    closeButton.addEventListener(
      "click",
      event => {
        event.preventDefault();
        event.stopPropagation();

        closeChat();
      }
    );
  }


  /* =========================================================
     MINIMIZE
     ========================================================= */

  if (minimizeButton) {
    minimizeButton.addEventListener(
      "click",
      event => {
        event.preventDefault();
        event.stopPropagation();

        if (isMinimized) {
          restoreChat();
        } else {
          minimizeChat();
        }
      }
    );
  }


  /* =========================================================
     NEW CHAT
     ========================================================= */

  if (newChatButton) {
    newChatButton.addEventListener(
      "click",
      event => {
        event.preventDefault();
        event.stopPropagation();

        newChat();
      }
    );
  }


  /* =========================================================
     FORM
     ========================================================= */

  if (chatForm) {
    chatForm.addEventListener(
      "submit",
      sendMessage
    );
  }


  if (messageInput) {
    messageInput.addEventListener(
      "keydown",
      event => {
        if (
          event.key === "Enter" &&
          !event.shiftKey
        ) {
          event.preventDefault();

          if (!isSending) {
            sendMessage(event);
          }
        }
      }
    );
  }


  /* =========================================================
     PARENT EVENTS
     ========================================================= */

  window.addEventListener(
    "message",
    event => {
      const data =
        event.data;

      if (!data) {
        return;
      }

      /*
       * Preview config is handled by the single
       * preview listener above.
       */

      switch (data.type) {
        case "widget:open":
          openChat();
          break;

        case "widget:close":
          closeChat();
          break;

        case "widget:minimize":
          minimizeChat();
          break;

        case "widget:restore":
          restoreChat();
          break;

        case "widget:new-chat":
          newChat();
          break;

        case "widget:config":
          config = {
            ...DEFAULT_CONFIG,
            ...(data.config || {})
          };

          applyConfig();
          break;

        default:
          break;
      }
    }
  );


  /* =========================================================
     INITIALIZE
     ========================================================= */

  async function initialize() {
    if (chatPanel) {
      chatPanel.classList.remove(
        "open",
        "is-open",
        "minimized",
        "is-minimized"
      );

      chatPanel.classList.add(
        "is-closed"
      );

      chatPanel.style.visibility =
        "hidden";

      chatPanel.style.opacity =
        "0";

      chatPanel.style.pointerEvents =
        "none";
    }

    document.body.classList.remove(
      "chat-open"
    );

    isOpen = false;
    isMinimized = false;

    updateMinimizeButton();

    setupPreviewMessaging();

    await loadWidgetConfig();

    loadActiveConversation();

    await registerVisitor();

    notifyParent(
      "widget:ready"
    );

    if (IS_PREVIEW) {
      setTimeout(() => {
        notifyParent(
          "widget:preview-ready"
        );
      }, 50);
    }
  }


  if (
    document.readyState ===
    "loading"
  ) {
    document.addEventListener(
      "DOMContentLoaded",
      initialize,
      {
        once: true
      }
    );
  } else {
    initialize();
  }

})();