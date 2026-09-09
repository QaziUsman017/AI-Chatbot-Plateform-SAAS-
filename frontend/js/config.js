const isLocal =
  window.location.hostname === "127.0.0.1" ||
  window.location.hostname === "localhost";

window.chatbotConfig = {
  apiBaseUrl: isLocal
    ? "http://127.0.0.1:8001"
    : "https://ai-chatbot-saas-three.vercel.app",

  widgetId: "ai-chatbot-platform-widget",

  streamingEnabled: false,
};