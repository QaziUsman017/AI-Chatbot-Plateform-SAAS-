const iframeManager = {

  // ======================================================
  // CREATE IFRAME
  // ======================================================

  createFrame({
    src,
    id = "ai-chatbot-platform-frame",
  } = {}) {

    if (!src) {
      console.error(
        "IframeManager: iframe source is required."
      );

      return null;
    }

    const existing =
      document.getElementById(id);

    if (existing) {
      return existing;
    }

    const iframe =
      document.createElement("iframe");

    iframe.id = id;

    iframe.src = src;

    iframe.title =
      "AI Chatbot";

    iframe.setAttribute(
      "allow",
      "clipboard-write"
    );

    iframe.setAttribute(
      "frameborder",
      "0"
    );

    iframe.setAttribute(
      "loading",
      "lazy"
    );

    Object.assign(
      iframe.style,
      {
        position: "fixed",

        top: "auto",
        left: "auto",
        right: "20px",
        bottom: "20px",

        width: "420px",
        height: "680px",

        maxWidth:
          "calc(100vw - 40px)",

        maxHeight:
          "calc(100vh - 40px)",

        border: "0",
        margin: "0",
        padding: "0",

        background:
          "transparent",

        zIndex:
          "2147483647",

        display:
          "block",

        pointerEvents:
          "auto",
      }
    );

    document.body.appendChild(
      iframe
    );

    this.applyResponsiveSize(
      iframe
    );

    return iframe;
  },


  // ======================================================
  // REMOVE IFRAME
  // ======================================================

  removeFrame(id) {

    const iframe =
      document.getElementById(id);

    if (iframe) {
      iframe.remove();
    }
  },


  // ======================================================
  // RESIZE
  // ======================================================

  resizeFrame(
    iframe,
    width = "420px",
    height = "680px"
  ) {

    if (!iframe) {
      return;
    }

    iframe.style.width =
      width;

    iframe.style.height =
      height;

    iframe.style.maxWidth =
      "calc(100vw - 40px)";

    iframe.style.maxHeight =
      "calc(100vh - 40px)";
  },


  // ======================================================
  // POSITION
  // ======================================================

  setPosition(
    iframe,
    left,
    top
  ) {

    if (!iframe) {
      return;
    }

    const rect =
      iframe.getBoundingClientRect();

    const width =
      rect.width;

    const height =
      rect.height;

    const maxLeft =
      Math.max(
        0,
        window.innerWidth -
          width
      );

    const maxTop =
      Math.max(
        0,
        window.innerHeight -
          height
      );

    const safeLeft =
      Math.max(
        0,
        Math.min(
          Number(left) || 0,
          maxLeft
        )
      );

    const safeTop =
      Math.max(
        0,
        Math.min(
          Number(top) || 0,
          maxTop
        )
      );

    iframe.style.left =
      `${safeLeft}px`;

    iframe.style.top =
      `${safeTop}px`;

    iframe.style.right =
      "auto";

    iframe.style.bottom =
      "auto";
  },


  // ======================================================
  // RESET POSITION
  // ======================================================

  resetPosition(
    iframe
  ) {

    if (!iframe) {
      return;
    }

    iframe.style.left =
      "auto";

    iframe.style.top =
      "auto";

    iframe.style.right =
      "20px";

    iframe.style.bottom =
      "20px";
  },


  // ======================================================
  // MOBILE
  // ======================================================

  makeMobile(
    iframe
  ) {

    if (!iframe) {
      return;
    }

    iframe.style.top =
      "0";

    iframe.style.left =
      "0";

    iframe.style.right =
      "0";

    iframe.style.bottom =
      "0";

    iframe.style.width =
      "100vw";

    iframe.style.height =
      "100vh";

    iframe.style.maxWidth =
      "none";

    iframe.style.maxHeight =
      "none";
  },


  // ======================================================
  // DESKTOP
  // ======================================================

  makeDesktop(
    iframe
  ) {

    if (!iframe) {
      return;
    }

    iframe.style.top =
      "auto";

    iframe.style.left =
      "auto";

    iframe.style.right =
      "20px";

    iframe.style.bottom =
      "20px";

    iframe.style.width =
      "420px";

    iframe.style.height =
      "680px";

    iframe.style.maxWidth =
      "calc(100vw - 40px)";

    iframe.style.maxHeight =
      "calc(100vh - 40px)";
  },


  // ======================================================
  // RESPONSIVE SIZE
  // ======================================================

  applyResponsiveSize(
    iframe
  ) {

    if (!iframe) {
      return;
    }

    const width =
      window.innerWidth;

    if (width <= 600) {

      this.makeMobile(
        iframe
      );

    } else {

      this.makeDesktop(
        iframe
      );
    }
  },


  // ======================================================
  // KEEP INSIDE VIEWPORT
  // ======================================================

  keepInsideViewport(
    iframe
  ) {

    if (!iframe) {
      return;
    }

    const rect =
      iframe.getBoundingClientRect();

    const maxLeft =
      Math.max(
        0,
        window.innerWidth -
          rect.width
      );

    const maxTop =
      Math.max(
        0,
        window.innerHeight -
          rect.height
      );

    const currentLeft =
      rect.left;

    const currentTop =
      rect.top;

    const newLeft =
      Math.max(
        0,
        Math.min(
          currentLeft,
          maxLeft
        )
      );

    const newTop =
      Math.max(
        0,
        Math.min(
          currentTop,
          maxTop
        )
      );

    this.setPosition(
      iframe,
      newLeft,
      newTop
    );
  },


  // ======================================================
  // INITIALIZE RESPONSIVE LISTENER
  // ======================================================

  watchResponsive(
    iframe
  ) {

    if (!iframe) {
      return;
    }

    const update =
      () => {

        this.applyResponsiveSize(
          iframe
        );

        this.keepInsideViewport(
          iframe
        );
      };

    window.addEventListener(
      "resize",
      update
    );
  },


  // ======================================================
  // POST MESSAGE
  // ======================================================

  sendMessage(
    iframe,
    type,
    data = {}
  ) {

    if (
      !iframe ||
      !iframe.contentWindow
    ) {
      return;
    }

    iframe.contentWindow.postMessage(
      {
        source:
          "ai-chatbot-widget-parent",

        type,

        ...data,
      },
      "*"
    );
  },

};