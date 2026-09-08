(function () {
    "use strict";

    const API_BASE_URL =
        window.chatbotConfig?.apiBaseUrl ||
        "http://127.0.0.1:8000";

    const TOKEN_KEY = "access_token";
    const USER_KEY = "user";
    const REQUEST_TIMEOUT = 15000;


    // =====================================================
    // TOKEN / USER
    // =====================================================

    function getAccessToken() {
        return (
            localStorage.getItem(TOKEN_KEY) || ""
        ).trim();
    }


    function getStoredUser() {
        try {
            const user =
                localStorage.getItem(USER_KEY);

            return user
                ? JSON.parse(user)
                : null;

        } catch (error) {
            console.error(
                "Failed to read stored user:",
                error
            );

            return null;
        }
    }


    function saveSession(data) {

        if (
            !data ||
            !data.access_token
        ) {
            throw new Error(
                "Authentication token was not returned by the server."
            );
        }

        const user = {
            user_id:
                data.user_id || null,

            email:
                data.email || null,

            full_name:
                data.full_name || null,

            role:
                data.role || "user",

            client_id:
                data.client_id || null,

            is_active: true
        };


        localStorage.setItem(
            TOKEN_KEY,
            data.access_token
        );

        localStorage.setItem(
            USER_KEY,
            JSON.stringify(user)
        );


        // Remove old / duplicate formats.

        sessionStorage.removeItem(
            "access_token"
        );

        sessionStorage.removeItem(
            "accessToken"
        );

        sessionStorage.removeItem(
            "token"
        );

        localStorage.removeItem(
            "accessToken"
        );

        localStorage.removeItem(
            "token"
        );


        return user;
    }


    function clearSession() {

        localStorage.removeItem(
            TOKEN_KEY
        );

        localStorage.removeItem(
            USER_KEY
        );

        localStorage.removeItem(
            "accessToken"
        );

        localStorage.removeItem(
            "token"
        );


        sessionStorage.removeItem(
            TOKEN_KEY
        );

        sessionStorage.removeItem(
            "accessToken"
        );

        sessionStorage.removeItem(
            "token"
        );

        sessionStorage.removeItem(
            USER_KEY
        );
    }


    function logout(
        redirect = true
    ) {

        clearSession();

        if (redirect) {
            window.location.href =
                "./login.html";
        }
    }


    // =====================================================
    // HEADERS
    // =====================================================

    function getAuthHeaders() {

        const token =
            getAccessToken();

        const headers = {
            "Content-Type":
                "application/json"
        };

        if (token) {
            headers.Authorization =
                `Bearer ${token}`;
        }

        return headers;
    }


    // =====================================================
    // FETCH WITH TIMEOUT
    // =====================================================

    async function fetchWithTimeout(
        url,
        options = {},
        timeout = REQUEST_TIMEOUT
    ) {

        const controller =
            new AbortController();

        const timeoutId =
            setTimeout(
                () => controller.abort(),
                timeout
            );

        try {

            return await fetch(
                url,
                {
                    ...options,
                    signal:
                        controller.signal
                }
            );

        } catch (error) {

            if (
                error?.name ===
                "AbortError"
            ) {
                throw new Error(
                    "Server request timed out. Please make sure the backend and MongoDB are running."
                );
            }

            throw error;

        } finally {

            clearTimeout(
                timeoutId
            );
        }
    }


    // =====================================================
    // RESPONSE PARSER
    // =====================================================

    async function parseResponse(
        response
    ) {

        let data = null;

        try {

            data =
                await response.json();

        } catch {

            data = null;
        }


        if (response.ok) {
            return data;
        }


        let message =
            "Something went wrong.";


        if (data) {

            if (
                typeof data.detail ===
                "string"
            ) {

                message =
                    data.detail;

            } else if (
                Array.isArray(
                    data.detail
                )
            ) {

                message =
                    data.detail
                        .map(item => {

                            if (
                                typeof item ===
                                "string"
                            ) {
                                return item;
                            }


                            if (item?.msg) {

                                const field =
                                    Array.isArray(
                                        item.loc
                                    )
                                        ? item.loc[
                                            item.loc.length - 1
                                        ]
                                        : "";

                                return field
                                    ? `${field}: ${item.msg}`
                                    : item.msg;
                            }


                            return JSON.stringify(
                                item
                            );
                        })
                        .join(", ");

            } else if (
                typeof data.message ===
                "string"
            ) {

                message =
                    data.message;
            }
        }


        const error =
            new Error(message);

        error.status =
            response.status;

        error.data =
            data;

        throw error;
    }


    // =====================================================
    // LOGIN
    // =====================================================

    async function loginUser(
        email,
        password
    ) {

        const cleanEmail =
            String(email || "")
                .trim()
                .toLowerCase();

        const cleanPassword =
            String(password || "");


        if (!cleanEmail) {
            throw new Error(
                "Please enter your email address."
            );
        }

        if (!cleanPassword) {
            throw new Error(
                "Please enter your password."
            );
        }


        let response;


        try {

            response =
                await fetchWithTimeout(
                    `${API_BASE_URL}/auth/login`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            email:
                                cleanEmail,

                            password:
                                cleanPassword
                        })
                    }
                );

        } catch (error) {

            console.error(
                "Login network error:",
                error
            );

            throw new Error(
                error?.message ||
                "Unable to connect to the server. Please make sure the backend is running."
            );
        }


        const data =
            await parseResponse(
                response
            );


        saveSession(data);

        return data;
    }


    // =====================================================
    // REGISTER
    // =====================================================

    async function registerUser(
        fullName,
        email,
        password,
        clientId = null
    ) {

        const cleanName =
            String(fullName || "")
                .trim();

        const cleanEmail =
            String(email || "")
                .trim()
                .toLowerCase();

        const cleanPassword =
            String(password || "");

        const cleanClientId =
            String(clientId || "")
                .trim();


        if (!cleanName) {
            throw new Error(
                "Please enter your full name."
            );
        }


        if (cleanName.length < 2) {
            throw new Error(
                "Full name must contain at least 2 characters."
            );
        }


        if (!cleanEmail) {
            throw new Error(
                "Please enter your email address."
            );
        }


        if (!cleanPassword) {
            throw new Error(
                "Please enter a password."
            );
        }


        if (cleanPassword.length < 8) {
            throw new Error(
                "Password must be at least 8 characters."
            );
        }


        const payload = {
            full_name:
                cleanName,

            email:
                cleanEmail,

            password:
                cleanPassword
        };


        if (cleanClientId) {
            payload.client_id =
                cleanClientId;
        }


        let response;


        try {

            response =
                await fetchWithTimeout(
                    `${API_BASE_URL}/auth/register`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify(
                                payload
                            )
                    }
                );

        } catch (error) {

            console.error(
                "Registration network error:",
                error
            );

            throw new Error(
                error?.message ||
                "Unable to connect to the server. Please make sure the backend is running."
            );
        }


        const data =
            await parseResponse(
                response
            );


        saveSession(data);

        return data;
    }


    // =====================================================
    // CURRENT USER
    // =====================================================

    async function getCurrentUser() {

        const token =
            getAccessToken();


        if (!token) {
            return null;
        }


        let response;


        try {

            response =
                await fetchWithTimeout(
                    `${API_BASE_URL}/auth/me`,
                    {
                        method: "GET",

                        headers:
                            getAuthHeaders()
                    }
                );

        } catch (error) {

            console.error(
                "Auth verification error:",
                error
            );

            return null;
        }


        if (
            response.status === 401
        ) {

            clearSession();

            return null;
        }


        if (!response.ok) {
            return null;
        }


        try {

            const user =
                await response.json();


            localStorage.setItem(
                USER_KEY,
                JSON.stringify(user)
            );


            return user;

        } catch (error) {

            console.error(
                "Failed to parse current user:",
                error
            );

            return null;
        }
    }


    // =====================================================
    // REQUIRE AUTHENTICATION
    // =====================================================

    async function requireAuthentication() {

        const token =
            getAccessToken();


        if (!token) {
            return null;
        }


        return await getCurrentUser();
    }


    // =====================================================
    // HELPERS
    // =====================================================

    function isAuthenticated() {
        return Boolean(
            getAccessToken()
        );
    }


    function getUser() {
        return getStoredUser();
    }


    function getClientId() {

        const user =
            getStoredUser();

        return user?.client_id ||
            null;
    }


    // =====================================================
    // PUBLIC API
    // =====================================================

    window.auth = {

        API_BASE_URL,

        getAccessToken,

        getAuthHeaders,

        getUser,

        getClientId,

        isAuthenticated,

        saveSession,

        clearSession,

        loginUser,

        registerUser,

        getCurrentUser,

        requireAuthentication,

        logout
    };


    // =====================================================
    // BACKWARD COMPATIBILITY
    // =====================================================

    window.loginUser =
        loginUser;

    window.registerUser =
        registerUser;

    window.logoutUser =
        logout;

})();