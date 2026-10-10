import { createStore } from "/js/AlpineStore.js";
import * as API from "/js/api.js";
import { toastFrontendError, toastFrontendSuccess } from "/components/notifications/notification-store.js";

const API_BASE = "/plugins/capsolver";

export const store = createStore("capsolverConfig", {
    didInit: false,
    testing: false,
    config: null,
    context: null,

    init(config, context) {
        this.config = config || {};
        this.context = context || {};
        this.didInit = true;
    },

    cleanup() {
        this.didInit = false;
        this.testing = false;
    },

    async testConnection() {
        if (this.testing) return;
        this.testing = true;
        try {
            const response = await API.fetchApi(`${API_BASE}/capsolver_test`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ api_key: this.config?.api_key || "" }),
            });
            const result = await response.json();
            if (result && result.success) {
                toastFrontendSuccess(
                    `Connected. Balance: ${result.balance}`,
                    "Capsolver"
                );
            } else {
                toastFrontendError(
                    (result && result.error) || "Connection test failed",
                    "Capsolver"
                );
            }
        } catch (e) {
            toastFrontendError(e?.message || "Connection test failed", "Capsolver");
        } finally {
            this.testing = false;
        }
    },
});
