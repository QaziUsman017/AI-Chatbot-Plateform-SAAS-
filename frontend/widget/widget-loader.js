(function () {
  "use strict";

  /* =========================================================
     SCRIPT CONFIG
  ========================================================= */

  const currentScript =
    document.currentScript;

  const API_BASE_URL =
    currentScript?.dataset?.apiUrl ||
    "http://127.0.0.1:8000";

  const CLIENT_ID =
    currentScript?.dataset?.clientId ||
    "";

  const WIDGET_ID =
    currentScript?.dataset?.widgetId ||
    "ai-chatbot-platform-widget";


  /* =========================================================
     CONSTANTS
  ========================================================= */

  const DESKTOP_OPEN_WIDTH = 420;
  const DESKTOP_OPEN_HEIGHT = 620;

  const DESKTOP_MINIMIZED_HEIGHT = 68;

  const DESKTOP_CLOSED_SIZE = 58;

  const DESKTOP_RIGHT = 24;
  const DESKTOP_LEFT = 24;

  const DESKTOP_TOP = 24;
  const DESKTOP_BOTTOM = 24;

  const MOBILE_BREAKPOINT = 768;

  const POSITION_STORAGE_PREFIX =
    "ai-chatbot-widget-position";

  const CONFIG_POSITION_STORAGE_PREFIX =
    "ai-chatbot-widget-config-position";


  /* =========================================================
     IFRAME
  ========================================================= */

  const iframe =
    document.createElement("iframe");

  iframe.id =
    WIDGET_ID;

  iframe.title =
    "AI Chatbot";

  iframe.setAttribute(
    "aria-label",
    "AI Chatbot"
  );

  iframe.setAttribute(
    "scrolling",
    "no"
  );

  iframe.setAttribute(
    "frameborder",
    "0"
  );

  iframe.setAttribute(
    "allow",
    "clipboard-write"
  );

  iframe.src =
    `${API_BASE_URL}/widget/frame?client_id=${encodeURIComponent(
      CLIENT_ID
    )}`;


  /* =========================================================
     IFRAME STYLE
  ========================================================= */

  Object.assign(
    iframe.style,
    {
      position: "fixed",

      margin: "0",
      padding: "0",

      border: "0",
      outline: "0",

      background: "transparent",

      display: "block",

      overflow: "hidden",

      boxSizing: "border-box",

      zIndex: "2147483647",

      touchAction: "none",

      transition:
        "width 0.25s ease, height 0.25s ease, left 0.2s ease, top 0.2s ease, right 0.2s ease, bottom 0.2s ease",
    }
  );


  /* =========================================================
     STATE
  ========================================================= */

  let isMobile =
    window.innerWidth <=
    MOBILE_BREAKPOINT;

  let mode =
    "closed";

  let customPosition =
    false;

  let configuredPosition =
    "bottom-right";

  let lastAppliedConfiguredPosition =
    "bottom-right";

  let frameWidth =
    DESKTOP_CLOSED_SIZE;

  let frameHeight =
    DESKTOP_CLOSED_SIZE;

  let left = null;
  let top = null;

  let right =
    DESKTOP_RIGHT;

  let bottom =
    DESKTOP_BOTTOM;


  /* =========================================================
     DRAG STATE
  ========================================================= */

  let dragging = false;

  let dragStartScreenX = 0;
  let dragStartScreenY = 0;

  let dragStartLeft = 0;
  let dragStartTop = 0;

  let dragRAF = null;

  let pendingX = null;
  let pendingY = null;


  /* =========================================================
     APPEND IFRAME
  ========================================================= */

  function appendWidget() {

    if (
      !document.body.contains(
        iframe
      )
    ) {
      document.body.appendChild(
        iframe
      );
    }
  }

  appendWidget();


  /* =========================================================
     HELPERS
  ========================================================= */

  function clamp(
    value,
    min,
    max
  ) {
    return Math.min(
      Math.max(
        value,
        min
      ),
      max
    );
  }


  function getRect() {
    return iframe.getBoundingClientRect();
  }


  function normalizePosition(
    value
  ) {

    const position =
      String(
        value ||
        "bottom-right"
      )
        .trim()
        .toLowerCase();

    const allowedPositions = [
      "bottom-right",
      "bottom-left",
      "top-right",
      "top-left",
    ];

    return allowedPositions.includes(
      position
    )
      ? position
      : "bottom-right";
  }


  /* =========================================================
     STORAGE
  ========================================================= */

  function getStorageKey() {

    return (
      POSITION_STORAGE_PREFIX +
      ":" +
      (
        CLIENT_ID ||
        "default"
      )
    );
  }


  function getConfiguredPositionStorageKey() {

    return (
      CONFIG_POSITION_STORAGE_PREFIX +
      ":" +
      (
        CLIENT_ID ||
        "default"
      )
    );
  }


  function saveConfiguredPosition() {

    if (isMobile) {
      return;
    }

    try {

      localStorage.setItem(
        getConfiguredPositionStorageKey(),
        configuredPosition
      );

    } catch (error) {

      console.warn(
        "[Widget Loader] Configured position could not be saved.",
        error
      );
    }
  }


  function getSavedConfiguredPosition() {

    try {

      return normalizePosition(
        localStorage.getItem(
          getConfiguredPositionStorageKey()
        )
      );

    } catch {

      return null;
    }
  }


  function saveCustomPosition() {

    if (
      isMobile ||
      !customPosition ||
      !Number.isFinite(left) ||
      !Number.isFinite(top)
    ) {
      return;
    }

    try {

      localStorage.setItem(
        getStorageKey(),
        JSON.stringify({
          left,
          top,
        })
      );

    } catch (error) {

      console.warn(
        "[Widget Loader] Position could not be saved.",
        error
      );
    }
  }


  function loadCustomPosition() {

    if (isMobile) {
      return false;
    }

    try {

      const saved =
        localStorage.getItem(
          getStorageKey()
        );

      if (!saved) {
        return false;
      }

      const data =
        JSON.parse(saved);

      const savedLeft =
        Number(data?.left);

      const savedTop =
        Number(data?.top);

      if (
        !Number.isFinite(
          savedLeft
        ) ||
        !Number.isFinite(
          savedTop
        )
      ) {
        return false;
      }

      left =
        clamp(
          savedLeft,
          0,
          Math.max(
            0,
            window.innerWidth -
              frameWidth
          )
        );

      top =
        clamp(
          savedTop,
          0,
          Math.max(
            0,
            window.innerHeight -
              frameHeight
          )
        );

      customPosition =
        true;

      return true;

    } catch {

      return false;
    }
  }


  function clearCustomPosition() {

    try {

      localStorage.removeItem(
        getStorageKey()
      );

    } catch {
      // Ignore storage errors.
    }
  }


  /* =========================================================
     APPLY POSITION
  ========================================================= */

  function applyPosition() {

    if (isMobile) {

      iframe.style.left =
        "0px";

      iframe.style.top =
        "0px";

      iframe.style.right =
        "auto";

      iframe.style.bottom =
        "auto";

      return;
    }

    if (customPosition) {

      const maxLeft =
        Math.max(
          0,
          window.innerWidth -
            frameWidth
        );

      const maxTop =
        Math.max(
          0,
          window.innerHeight -
            frameHeight
        );

      left =
        clamp(
          Number(left) || 0,
          0,
          maxLeft
        );

      top =
        clamp(
          Number(top) || 0,
          0,
          maxTop
        );

      iframe.style.left =
        `${left}px`;

      iframe.style.top =
        `${top}px`;

      iframe.style.right =
        "auto";

      iframe.style.bottom =
        "auto";

      return;
    }

    iframe.style.left =
      "auto";

    iframe.style.top =
      "auto";

    iframe.style.right =
      right !== null
        ? `${right}px`
        : "auto";

    iframe.style.bottom =
      bottom !== null
        ? `${bottom}px`
        : "auto";
  }


  /* =========================================================
     CONFIGURED POSITION
  ========================================================= */

  function applyConfiguredPosition() {

    if (isMobile) {
      return;
    }

    configuredPosition =
      normalizePosition(
        configuredPosition
      );

    /*
     * Configuration position always means
     * a fixed screen corner.
     *
     * Therefore custom drag position is
     * disabled when applying dashboard
     * configuration.
     */
    customPosition =
      false;

    left = null;
    top = null;

    switch (
      configuredPosition
    ) {

      case "top-left":

        left =
          DESKTOP_LEFT;

        top =
          DESKTOP_TOP;

        right =
          null;

        bottom =
          null;

        break;


      case "top-right":

        left =
          null;

        top =
          DESKTOP_TOP;

        right =
          DESKTOP_RIGHT;

        bottom =
          null;

        break;


      case "bottom-left":

        left =
          DESKTOP_LEFT;

        top =
          null;

        right =
          null;

        bottom =
          DESKTOP_BOTTOM;

        break;


      case "bottom-right":

      default:

        left =
          null;

        top =
          null;

        right =
          DESKTOP_RIGHT;

        bottom =
          DESKTOP_BOTTOM;

        break;
    }

    lastAppliedConfiguredPosition =
      configuredPosition;

    saveConfiguredPosition();

    applyPosition();
  }


  /* =========================================================
     APPLY CONFIG POSITION ONLY IF NEEDED
  ========================================================= */

  function applyNewConfiguredPosition(
    newPosition
  ) {

    const normalized =
      normalizePosition(
        newPosition
      );

    const positionChanged =
      normalized !==
      configuredPosition;

    configuredPosition =
      normalized;

    /*
     * If dashboard configuration changed,
     * remove any previous dragged position.
     */
    if (positionChanged) {

      customPosition =
        false;

      left =
        null;

      top =
        null;

      clearCustomPosition();
    }

    applyConfiguredPosition();
  }


  /* =========================================================
     DESKTOP SIZE
  ========================================================= */

  function applyDesktopSize() {

    iframe.style.maxWidth =
      "calc(100vw - 48px)";

    iframe.style.maxHeight =
      "calc(100vh - 48px)";

    if (
      mode === "open"
    ) {

      frameWidth =
        DESKTOP_OPEN_WIDTH;

      frameHeight =
        DESKTOP_OPEN_HEIGHT;

    } else if (
      mode === "minimized"
    ) {

      frameWidth =
        DESKTOP_OPEN_WIDTH;

      frameHeight =
        DESKTOP_MINIMIZED_HEIGHT;

    } else {

      mode =
        "closed";

      frameWidth =
        DESKTOP_CLOSED_SIZE;

      frameHeight =
        DESKTOP_CLOSED_SIZE;
    }

    iframe.style.width =
      `${frameWidth}px`;

    iframe.style.height =
      `${frameHeight}px`;

    applyPosition();
  }


  /* =========================================================
     MOBILE SIZE
  ========================================================= */

  function applyMobileSize() {

    iframe.style.width =
      "100vw";

    iframe.style.height =
      "100dvh";

    iframe.style.maxWidth =
      "100vw";

    iframe.style.maxHeight =
      "100dvh";

    iframe.style.left =
      "0px";

    iframe.style.top =
      "0px";

    iframe.style.right =
      "auto";

    iframe.style.bottom =
      "auto";
  }


  /* =========================================================
     OPEN
  ========================================================= */

  function openFrame() {

    const previousMode =
      mode;

    mode =
      "open";

    if (isMobile) {

      applyMobileSize();

      return;
    }

    const rect =
      getRect();

    frameWidth =
      DESKTOP_OPEN_WIDTH;

    frameHeight =
      DESKTOP_OPEN_HEIGHT;

    iframe.style.width =
      `${frameWidth}px`;

    iframe.style.height =
      `${frameHeight}px`;

    /*
     * If the user manually dragged the widget,
     * keep that custom position.
     */
    if (customPosition) {

      if (
        previousMode === "minimized"
      ) {

        const bottomEdge =
          rect.bottom;

        left =
          clamp(
            rect.left,
            0,
            Math.max(
              0,
              window.innerWidth -
                frameWidth
            )
          );

        top =
          clamp(
            bottomEdge -
              frameHeight,
            0,
            Math.max(
              0,
              window.innerHeight -
                frameHeight
            )
          );

      } else {

        left =
          clamp(
            rect.left,
            0,
            Math.max(
              0,
              window.innerWidth -
                frameWidth
            )
          );

        top =
          clamp(
            rect.top,
            0,
            Math.max(
              0,
              window.innerHeight -
                frameHeight
            )
          );
      }

      applyPosition();

      return;
    }

    /*
     * Otherwise use dashboard configuration.
     */
    applyConfiguredPosition();
  }


  /* =========================================================
     MINIMIZE
  ========================================================= */

  function minimizeFrame() {

    if (
      mode === "closed"
    ) {
      return;
    }

    const rect =
      getRect();

    const bottomEdge =
      rect.bottom;

    mode =
      "minimized";

    if (isMobile) {

      applyMobileSize();

      return;
    }

    frameWidth =
      DESKTOP_OPEN_WIDTH;

    frameHeight =
      DESKTOP_MINIMIZED_HEIGHT;

    iframe.style.width =
      `${frameWidth}px`;

    iframe.style.height =
      `${frameHeight}px`;

    if (customPosition) {

      left =
        clamp(
          rect.left,
          0,
          Math.max(
            0,
            window.innerWidth -
              frameWidth
          )
        );

      top =
        clamp(
          bottomEdge -
            frameHeight,
          0,
          Math.max(
            0,
            window.innerHeight -
              frameHeight
          )
        );

      applyPosition();

      saveCustomPosition();

      return;
    }

    /*
     * Configured corner remains anchored.
     */
    applyConfiguredPosition();
  }


  /* =========================================================
     CLOSE
  ========================================================= */

  function closeFrame() {

    mode =
      "closed";

    if (isMobile) {

      applyMobileSize();

      return;
    }

    const rect =
      getRect();

    frameWidth =
      DESKTOP_CLOSED_SIZE;

    frameHeight =
      DESKTOP_CLOSED_SIZE;

    iframe.style.width =
      `${frameWidth}px`;

    iframe.style.height =
      `${frameHeight}px`;

    if (customPosition) {

      const bottomEdge =
        rect.bottom;

      left =
        clamp(
          rect.left,
          0,
          Math.max(
            0,
            window.innerWidth -
              frameWidth
          )
        );

      top =
        clamp(
          bottomEdge -
            frameHeight,
          0,
          Math.max(
            0,
            window.innerHeight -
              frameHeight
          )
        );

      applyPosition();

      return;
    }

    applyConfiguredPosition();
  }


  /* =========================================================
     RESIZE
  ========================================================= */

  function resizeFrame(
    width,
    height
  ) {

    if (isMobile) {

      applyMobileSize();

      return;
    }

    const newWidth =
      Number.parseFloat(
        width
      );

    const newHeight =
      Number.parseFloat(
        height
      );

    if (
      !Number.isFinite(
        newWidth
      ) ||
      !Number.isFinite(
        newHeight
      )
    ) {
      return;
    }

    const rect =
      getRect();

    frameWidth =
      newWidth;

    frameHeight =
      newHeight;

    iframe.style.width =
      `${frameWidth}px`;

    iframe.style.height =
      `${frameHeight}px`;

    if (customPosition) {

      left =
        clamp(
          rect.left,
          0,
          Math.max(
            0,
            window.innerWidth -
              frameWidth
          )
        );

      top =
        clamp(
          rect.top,
          0,
          Math.max(
            0,
            window.innerHeight -
              frameHeight
          )
        );

      applyPosition();

      return;
    }

    applyConfiguredPosition();
  }


  /* =========================================================
     DRAG START
  ========================================================= */

  function startDrag(data) {

    if (isMobile) {
      return;
    }

    const screenX =
      Number(
        data?.screenX
      );

    const screenY =
      Number(
        data?.screenY
      );

    if (
      !Number.isFinite(
        screenX
      ) ||
      !Number.isFinite(
        screenY
      )
    ) {
      return;
    }

    const rect =
      getRect();

    dragStartScreenX =
      screenX;

    dragStartScreenY =
      screenY;

    dragStartLeft =
      rect.left;

    dragStartTop =
      rect.top;

    left =
      rect.left;

    top =
      rect.top;

    /*
     * Dragging intentionally switches
     * the widget into custom positioning.
     */
    customPosition =
      true;

    dragging =
      true;

    iframe.style.transition =
      "none";

    iframe.style.left =
      `${left}px`;

    iframe.style.top =
      `${top}px`;

    iframe.style.right =
      "auto";

    iframe.style.bottom =
      "auto";
  }


  /* =========================================================
     DRAG MOVE
  ========================================================= */

  function moveDrag(data) {

    if (
      !dragging ||
      isMobile
    ) {
      return;
    }

    const screenX =
      Number(
        data?.screenX
      );

    const screenY =
      Number(
        data?.screenY
      );

    if (
      !Number.isFinite(
        screenX
      ) ||
      !Number.isFinite(
        screenY
      )
    ) {
      return;
    }

    pendingX =
      screenX;

    pendingY =
      screenY;

    if (
      dragRAF !== null
    ) {
      return;
    }

    dragRAF =
      requestAnimationFrame(
        () => {

          dragRAF =
            null;

          if (!dragging) {
            return;
          }

          const dx =
            pendingX -
            dragStartScreenX;

          const dy =
            pendingY -
            dragStartScreenY;

          const maxLeft =
            Math.max(
              0,
              window.innerWidth -
                frameWidth
            );

          const maxTop =
            Math.max(
              0,
              window.innerHeight -
                frameHeight
            );

          left =
            clamp(
              dragStartLeft +
                dx,
              0,
              maxLeft
            );

          top =
            clamp(
              dragStartTop +
                dy,
              0,
              maxTop
            );

          iframe.style.left =
            `${left}px`;

          iframe.style.top =
            `${top}px`;

          iframe.style.right =
            "auto";

          iframe.style.bottom =
            "auto";
        }
      );
  }


  /* =========================================================
     DRAG END
  ========================================================= */

  function endDrag() {

    if (!dragging) {
      return;
    }

    dragging =
      false;

    if (
      dragRAF !== null
    ) {

      cancelAnimationFrame(
        dragRAF
      );

      dragRAF =
        null;
    }

    iframe.style.transition =
      "width 0.25s ease, height 0.25s ease, left 0.2s ease, top 0.2s ease, right 0.2s ease, bottom 0.2s ease";

    applyPosition();

    saveCustomPosition();
  }


  /* =========================================================
     RESET POSITION
  ========================================================= */

  function resetPosition() {

    dragging =
      false;

    customPosition =
      false;

    left =
      null;

    top =
      null;

    right =
      DESKTOP_RIGHT;

    bottom =
      DESKTOP_BOTTOM;

    clearCustomPosition();

    applyConfiguredPosition();
  }


  /* =========================================================
     CONFIG FETCH
  ========================================================= */

  async function loadWidgetConfig() {

    if (!CLIENT_ID) {
      return;
    }

    try {

      const response =
        await fetch(
          `${API_BASE_URL}/widget/config?client_id=${encodeURIComponent(
            CLIENT_ID
          )}`,
          {
            method: "GET",

            headers: {
              Accept:
                "application/json",
            },

            cache:
              "no-store",
          }
        );

      if (!response.ok) {

        console.warn(
          `[Widget Loader] Config request failed: ${response.status}`
        );

        /*
         * Keep the safe default.
         */
        configuredPosition =
          "bottom-right";

        applyConfiguredPosition();

        return;
      }

      const data =
        await response.json();

      const config =
        data.config ||
        data;

      const serverPosition =
        normalizePosition(
          config.position
        );

      /*
       * IMPORTANT:
       *
       * Server/dashboard configuration
       * is authoritative.
       */
      configuredPosition =
        serverPosition;

      /*
       * Check whether this is a newly
       * configured position.
       */
      const savedConfiguredPosition =
        getSavedConfiguredPosition();

      if (
        savedConfiguredPosition !==
        serverPosition
      ) {

        /*
         * Dashboard position changed.
         *
         * Remove old dragged position so
         * the new corner takes effect.
         */
        customPosition =
          false;

        left =
          null;

        top =
          null;

        clearCustomPosition();

        saveConfiguredPosition();

        applyConfiguredPosition();

        return;
      }

      /*
       * Same configuration as before.
       *
       * Allow previously dragged position.
       */
      if (
        !loadCustomPosition()
      ) {

        customPosition =
          false;

        applyConfiguredPosition();

      } else {

        applyPosition();
      }

    } catch (error) {

      console.warn(
        "[Widget Loader] Could not load widget configuration.",
        error
      );

      /*
       * Safe fallback.
       */
      configuredPosition =
        "bottom-right";

      customPosition =
        false;

      clearCustomPosition();

      applyConfiguredPosition();
    }
  }


  /* =========================================================
     MESSAGE HANDLER
  ========================================================= */

  window.addEventListener(
    "message",
    function (event) {

      if (
        event.source !==
        iframe.contentWindow
      ) {
        return;
      }

      const data =
        event.data;

      if (
        !data ||
        data.source !==
          "ai-chatbot-widget"
      ) {
        return;
      }

      switch (
        data.type
      ) {

        case "widget:init":

          iframe.contentWindow.postMessage(
            {
              source:
                "ai-chatbot-widget-parent",

              type:
                "widget:init",

              clientId:
                CLIENT_ID,
            },
            "*"
          );

          break;


        case "widget:ready":

          break;


        case "widget:config":

          if (
            data.config
          ) {

            if (
              data.config.position
            ) {

              applyNewConfiguredPosition(
                data.config.position
              );
            }
          }

          break;


        case "widget:open":

          openFrame();

          break;


        case "widget:close":

          closeFrame();

          break;


        case "widget:minimize":

          minimizeFrame();

          break;


        case "widget:restore":

          openFrame();

          break;


        case "widget:new-chat":

          openFrame();

          break;


        case "widget:resize":

          resizeFrame(
            data.width,
            data.height
          );

          break;


        case "widget:drag":

          if (!dragging) {

            startDrag({
              screenX:
                data.screenX,

              screenY:
                data.screenY,
            });
          }

          moveDrag({
            screenX:
              data.screenX,

            screenY:
              data.screenY,
          });

          break;


        case "widget:drag-start":

          startDrag(data);

          break;


        case "widget:drag-move":

          moveDrag(data);

          break;


        case "widget:drag-end":

          endDrag();

          break;


        case "widget:reset-position":

          resetPosition();

          break;


        case "widget:position":

          if (isMobile) {
            break;
          }

          if (
            Number.isFinite(
              Number(data.left)
            ) &&
            Number.isFinite(
              Number(data.top)
            )
          ) {

            customPosition =
              true;

            left =
              clamp(
                Number(data.left),
                0,
                Math.max(
                  0,
                  window.innerWidth -
                    frameWidth
                )
              );

            top =
              clamp(
                Number(data.top),
                0,
                Math.max(
                  0,
                  window.innerHeight -
                    frameHeight
                )
              );

            applyPosition();

            saveCustomPosition();
          }

          break;
      }
    }
  );


  /* =========================================================
     IFRAME LOAD
  ========================================================= */

  iframe.addEventListener(
    "load",
    function () {

      iframe.contentWindow?.postMessage(
        {
          source:
            "ai-chatbot-widget-parent",

          type:
            "widget:init",

          clientId:
            CLIENT_ID,
        },
        "*"
      );
    }
  );


  /* =========================================================
     RESIZE
  ========================================================= */

  let resizeTimer =
    null;

  window.addEventListener(
    "resize",
    function () {

      clearTimeout(
        resizeTimer
      );

      resizeTimer =
        setTimeout(
          function () {

            const nextMobile =
              window.innerWidth <=
              MOBILE_BREAKPOINT;

            if (
              nextMobile !==
              isMobile
            ) {

              isMobile =
                nextMobile;

              dragging =
                false;

              if (
                isMobile
              ) {

                applyMobileSize();

              } else {

                applyDesktopSize();

                if (
                  customPosition
                ) {

                  applyPosition();

                } else {

                  applyConfiguredPosition();
                }
              }

              return;
            }

            if (!isMobile) {

              if (
                customPosition
              ) {

                left =
                  clamp(
                    Number(left) || 0,
                    0,
                    Math.max(
                      0,
                      window.innerWidth -
                        frameWidth
                    )
                  );

                top =
                  clamp(
                    Number(top) || 0,
                    0,
                    Math.max(
                      0,
                      window.innerHeight -
                        frameHeight
                    )
                  );

                applyPosition();

                saveCustomPosition();

              } else {

                applyDesktopSize();
              }
            }

          },
          100
        );
    }
  );


  /* =========================================================
     INITIALIZE
  ========================================================= */

  if (isMobile) {

    applyMobileSize();

  } else {

    mode =
      "closed";

    applyDesktopSize();

    /*
     * Start from configured position.
     *
     * loadWidgetConfig() will later determine
     * whether a previously dragged custom position
     * should be restored.
     */
    customPosition =
      false;

    applyConfiguredPosition();
  }


  /* =========================================================
     LOAD CONFIG
  ========================================================= */

  loadWidgetConfig();


  /* =========================================================
     PUBLIC API
  ========================================================= */

  window.AIChatbotWidgetFrame = {

    iframe,

    open:
      openFrame,

    close:
      closeFrame,

    minimize:
      minimizeFrame,

    resetPosition:
      resetPosition,

    setPosition:
      function (
        newLeft,
        newTop
      ) {

        if (isMobile) {
          return;
        }

        customPosition =
          true;

        left =
          clamp(
            Number(newLeft) || 0,
            0,
            Math.max(
              0,
              window.innerWidth -
                frameWidth
            )
          );

        top =
          clamp(
            Number(newTop) || 0,
            0,
            Math.max(
              0,
              window.innerHeight -
                frameHeight
            )
          );

        applyPosition();

        saveCustomPosition();
      },
  };


  /* =========================================================
     CONFIG
  ========================================================= */

  window.AIChatbotWidgetConfig = {

    apiBaseUrl:
      API_BASE_URL,

    clientId:
      CLIENT_ID,
  };


  /* =========================================================
     READY
  ========================================================= */

  console.log(
    "[Widget Loader] AI Chatbot Widget loaded successfully.",
    {
      clientId:
        CLIENT_ID,

      apiBaseUrl:
        API_BASE_URL,

      dragEnabled:
        true,

      position:
        configuredPosition,
    }
  );

})();