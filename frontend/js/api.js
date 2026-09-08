(function () {

  "use strict";


  // ======================================================
  // API BASE URL
  // ======================================================

  const API_BASE_URL =
    "https://fastapi-five-alpha.vercel.app";


  // ======================================================
  // GET ACCESS TOKEN
  // ======================================================

  function getAccessToken() {

    const token =
      localStorage.getItem(
        "access_token"
      );


    if (!token) {
      return null;
    }


    const cleanedToken =
      token.trim();


    if (!cleanedToken) {
      return null;
    }


    return cleanedToken;
  }


  // ======================================================
  // AUTH HEADERS
  // ======================================================

  function getAuthHeaders() {

    const token =
      getAccessToken();


    if (!token) {

      return {
        "Content-Type":
          "application/json"
      };
    }


    return {

      "Content-Type":
        "application/json",

      "Authorization":
        `Bearer ${token}`

    };
  }


  // ======================================================
  // REQUIRE TOKEN
  // ======================================================

  function requireToken() {

    const token =
      getAccessToken();


    if (!token) {

      throw new Error(
        "Not authenticated"
      );
    }


    return token;
  }


  // ======================================================
  // WIDGET CLIENT ID
  // ======================================================

  function getWidgetClientId() {

    const params =
      new URLSearchParams(
        window.location.search
      );


    return (
      params.get("client_id") ||
      ""
    ).trim();
  }


  // ======================================================
  // PARSE RESPONSE
  // ======================================================

  async function parseResponse(
    response
  ) {

    const rawText =
      await response.text();


    let data = {};


    if (rawText) {

      try {

        data =
          JSON.parse(
            rawText
          );

      } catch (_) {

        data = {
          raw: rawText
        };
      }
    }


    return {
      data,
      rawText
    };
  }


  // ======================================================
  // API
  // ======================================================

  window.api = {


    // ====================================================
    // NORMAL CHAT
    // ====================================================

    async sendMessage(payload) {

      const token =
        requireToken();


      console.log(
        "===================================="
      );

      console.log(
        "[API] Sending authenticated /chat request"
      );

      console.log(
        "[API] URL:",
        `${API_BASE_URL}/chat`
      );

      console.log(
        "[API] Token exists:",
        Boolean(token)
      );

      console.log(
        "[API] Token length:",
        token.length
      );

      console.log(
        "[API] Payload:",
        payload
      );


      const response =
        await fetch(
          `${API_BASE_URL}/chat`,
          {

            method:
              "POST",

            headers: {

              "Content-Type":
                "application/json",

              "Authorization":
                `Bearer ${token}`

            },

            body:
              JSON.stringify(
                payload
              )

          }
        );


      const {
        data,
        rawText
      } =
        await parseResponse(
          response
        );


      console.log(
        "[API] /chat HTTP STATUS:",
        response.status
      );

      console.log(
        "[API] /chat RAW RESPONSE:",
        rawText
      );

      console.log(
        "[API] /chat PARSED RESPONSE:",
        data
      );


      // --------------------------------------------------
      // UNAUTHORIZED
      // --------------------------------------------------

      if (
        response.status === 401
      ) {

        console.error(
          "[API] Authentication failed."
        );


        throw new Error(
          data?.detail ||
          data?.message ||
          "Not authenticated"
        );
      }


      // --------------------------------------------------
      // OTHER ERROR
      // --------------------------------------------------

      if (!response.ok) {

        const detail =
          data?.detail ||
          data?.message ||
          data?.error ||
          `Backend request failed: ${response.status}`;


        throw new Error(
          typeof detail === "string"
            ? detail
            : JSON.stringify(detail)
        );
      }


      // --------------------------------------------------
      // SUCCESS
      // --------------------------------------------------

      return data;
    },


    // ====================================================
    // DOCUMENT UPLOAD
    // ====================================================

    async uploadDocument(
      file,
      clientId
    ) {

      const token =
        requireToken();


      if (!file) {

        throw new Error(
          "Please select a document."
        );
      }


      if (!clientId) {

        throw new Error(
          "Client ID not found."
        );
      }


      console.log(
        "===================================="
      );

      console.log(
        "[API] Uploading document"
      );

      console.log(
        "[API] URL:",
        `${API_BASE_URL}/upload`
      );

      console.log(
        "[API] CLIENT ID:",
        clientId
      );

      console.log(
        "[API] FILE:",
        file.name
      );


      // --------------------------------------------------
      // FORM DATA
      // --------------------------------------------------

      const formData =
        new FormData();


      formData.append(
        "client_id",
        clientId
      );


      formData.append(
        "file",
        file,
        file.name
      );


      const response =
        await fetch(
          `${API_BASE_URL}/upload`,
          {

            method:
              "POST",

            headers: {

              "Authorization":
                `Bearer ${token}`

            },

            body:
              formData

          }
        );


      const {
        data,
        rawText
      } =
        await parseResponse(
          response
        );


      console.log(
        "[API] UPLOAD HTTP STATUS:",
        response.status
      );

      console.log(
        "[API] UPLOAD RESPONSE:",
        data
      );


      // --------------------------------------------------
      // AUTH ERROR
      // --------------------------------------------------

      if (
        response.status === 401
      ) {

        throw new Error(
          data?.detail ||
          data?.message ||
          "Not authenticated"
        );
      }


      // --------------------------------------------------
      // OTHER ERROR
      // --------------------------------------------------

      if (!response.ok) {

        const detail =
          data?.detail ||
          data?.message ||
          data?.error ||
          `Document upload failed: ${response.status}`;


        throw new Error(
          typeof detail === "string"
            ? detail
            : JSON.stringify(detail)
        );
      }


      return data;
    },


    // ====================================================
    // WIDGET CHAT
    // ====================================================

    async sendWidgetMessage(
      message,
      conversationHistory = []
    ) {

      const clientId =
        getWidgetClientId();


      if (!clientId) {

        throw new Error(
          "Widget client ID not found."
        );
      }


      console.log(
        "===================================="
      );

      console.log(
        "[API] Sending widget chat request"
      );

      console.log(
        "[API] URL:",
        `${API_BASE_URL}/widget/chat`
      );

      console.log(
        "[API] CLIENT ID:",
        clientId
      );


      /*
       * IMPORTANT:
       *
       * Widget chat does NOT require
       * the dashboard JWT.
       *
       * The widget identifies the client
       * using client_id.
       */

      const response =
        await fetch(
          `${API_BASE_URL}/widget/chat`,
          {

            method:
              "POST",

            headers: {

              "Content-Type":
                "application/json",

              "Accept":
                "application/json"

            },

            body:
              JSON.stringify({

                message,

                client_id:
                  clientId,

                conversation_history:
                  conversationHistory

              })

          }
        );


      const {
        data,
        rawText
      } =
        await parseResponse(
          response
        );


      console.log(
        "[API] WIDGET HTTP STATUS:",
        response.status
      );

      console.log(
        "[API] WIDGET RESPONSE:",
        data
      );


      if (!response.ok) {

        const detail =
          data?.detail ||
          data?.message ||
          data?.error ||
          `Widget request failed: ${response.status}`;


        throw new Error(
          typeof detail === "string"
            ? detail
            : JSON.stringify(detail)
        );
      }


      return data;
    },


    // ====================================================
    // CHAT HISTORY
    // ====================================================

    async getChatHistory() {

      const token =
        requireToken();


      const response =
        await fetch(
          `${API_BASE_URL}/chat/history`,
          {

            method:
              "GET",

            headers: {

              "Content-Type":
                "application/json",

              "Authorization":
                `Bearer ${token}`

            }

          }
        );


      const {
        data
      } =
        await parseResponse(
          response
        );


      console.log(
        "[API] HISTORY STATUS:",
        response.status
      );


      if (
        response.status === 401
      ) {

        throw new Error(
          data?.detail ||
          data?.message ||
          "Not authenticated"
        );
      }


      if (!response.ok) {

        throw new Error(
          data?.detail ||
          data?.message ||
          `History request failed: ${response.status}`
        );
      }


      return data;
    },


    // ====================================================
    // GET CONVERSATION
    // ====================================================

    async getConversation(
      conversationId
    ) {

      const token =
        requireToken();


      const response =
        await fetch(
          `${API_BASE_URL}/chat/${encodeURIComponent(
            conversationId
          )}`,
          {

            method:
              "GET",

            headers: {

              "Content-Type":
                "application/json",

              "Authorization":
                `Bearer ${token}`

            }

          }
        );


      const {
        data
      } =
        await parseResponse(
          response
        );


      if (
        response.status === 401
      ) {

        throw new Error(
          data?.detail ||
          data?.message ||
          "Not authenticated"
        );
      }


      if (
        response.status === 404
      ) {

        throw new Error(
          "Conversation not found"
        );
      }


      if (!response.ok) {

        throw new Error(
          data?.detail ||
          data?.message ||
          `Conversation request failed: ${response.status}`
        );
      }


      return data;
    },


    // ====================================================
    // DELETE CONVERSATION
    // ====================================================

    async deleteConversation(
      conversationId
    ) {

      const token =
        requireToken();


      const response =
        await fetch(
          `${API_BASE_URL}/chat/${encodeURIComponent(
            conversationId
          )}`,
          {

            method:
              "DELETE",

            headers: {

              "Content-Type":
                "application/json",

              "Authorization":
                `Bearer ${token}`

            }

          }
        );


      const {
        data
      } =
        await parseResponse(
          response
        );


      if (
        response.status === 401
      ) {

        throw new Error(
          data?.detail ||
          data?.message ||
          "Not authenticated"
        );
      }


      if (
        response.status === 404
      ) {

        throw new Error(
          "Conversation not found"
        );
      }


      if (!response.ok) {

        throw new Error(
          data?.detail ||
          data?.message ||
          `Delete request failed: ${response.status}`
        );
      }


      return data;
    },


    // ====================================================
    // RESET CHAT
    // ====================================================

    async resetChat() {

      const token =
        requireToken();


      const response =
        await fetch(
          `${API_BASE_URL}/chat/reset`,
          {

            method:
              "POST",

            headers: {

              "Content-Type":
                "application/json",

              "Authorization":
                `Bearer ${token}`

            }

          }
        );


      const {
        data
      } =
        await parseResponse(
          response
        );


      if (
        response.status === 401
      ) {

        throw new Error(
          data?.detail ||
          data?.message ||
          "Not authenticated"
        );
      }


      if (!response.ok) {

        throw new Error(
          data?.detail ||
          data?.message ||
          `Reset request failed: ${response.status}`
        );
      }


      return data;
    }

  };


  // ======================================================
  // INITIAL DEBUG
  // ======================================================

  console.log(
    "[API] API module initialized."
  );

  console.log(
    "[API] Base URL:",
    API_BASE_URL
  );

  console.log(
    "[API] Access token available:",
    Boolean(getAccessToken())
  );

})();