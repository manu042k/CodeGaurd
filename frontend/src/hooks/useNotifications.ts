"use client";

import { useState, useCallback } from "react";

interface NotificationState {
  id: string;
  message: string;
  type: "success" | "error";
}

export function useNotifications() {
  const [notifications, setNotifications] = useState<NotificationState[]>([]);

  const showNotification = useCallback(
    (message: string, type: "success" | "error" = "success") => {
      const id = Date.now().toString();
      setNotifications((prev) => [...prev, { id, message, type }]);
    },
    []
  );

  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const showSuccess = useCallback(
    (message: string) => showNotification(message, "success"),
    [showNotification]
  );

  const showError = useCallback(
    (message: string) => showNotification(message, "error"),
    [showNotification]
  );

  return {
    notifications,
    showNotification,
    showSuccess,
    showError,
    removeNotification,
  };
}
