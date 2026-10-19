import apiClient from "../api/axios";

// Helper to convert base64 url VAPID key to Uint8Array
function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, "+")
    .replace(/_/g, "/");

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export const pushService = {
  getVapidPublicKey: async () => {
    try {
      const res = await apiClient.get("/push/vapid-public-key");
      return res.data?.public_key || "";
    } catch (err) {
      return "";
    }
  },

  subscribeUser: async () => {
    if (typeof window === "undefined") return null;
    if (!("serviceWorker" in navigator) || !("PushManager" in window) || !("Notification" in window)) {
      return null;
    }

    try {
      // 1. Check/request Notification permission
      let permission = Notification.permission;
      if (permission === "default") {
        permission = await Notification.requestPermission();
      }

      if (permission !== "granted") {
        return null;
      }

      // 2. Fetch VAPID key from backend
      const res = await apiClient.get("/push/vapid-public-key");
      const publicKey = res.data?.public_key;
      if (!publicKey) {
        // VAPID keys not configured on backend; degrade gracefully
        return null;
      }

      // 3. Register push with Service Worker PushManager
      const registration = await navigator.serviceWorker.ready;
      let subscription = await registration.pushManager.getSubscription();

      if (!subscription) {
        subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(publicKey),
        });
      }

      // 4. Send subscription to backend
      const subJson = subscription.toJSON();
      await apiClient.post("/push/subscribe", {
        endpoint: subscription.endpoint,
        p256dh: subJson.keys?.p256dh,
        auth: subJson.keys?.auth,
      });

      return subscription;
    } catch (err) {
      console.warn("Web Push subscription setup skipped or failed:", err);
      return null;
    }
  },

  unsubscribeUser: async () => {
    if (typeof window === "undefined" || !("serviceWorker" in navigator)) return;

    try {
      const registration = await navigator.serviceWorker.getRegistration();
      if (!registration || !registration.pushManager) return;
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        await apiClient.post("/push/unsubscribe", {
          endpoint: subscription.endpoint,
        });
        await subscription.unsubscribe();
      }
    } catch (err) {
      console.warn("Web Push unsubscribe failed:", err);
    }
  },
};
