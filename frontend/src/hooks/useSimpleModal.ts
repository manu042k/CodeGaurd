"use client";

import { useState, useCallback } from "react";

interface ConfirmationConfig {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: "danger" | "warning" | "info";
  onConfirm: () => void | Promise<void>;
}

export function useSimpleModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [config, setConfig] = useState<ConfirmationConfig | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const openModal = useCallback((modalConfig: ConfirmationConfig) => {
    setConfig(modalConfig);
    setIsOpen(true);
    setIsLoading(false);
  }, []);

  const closeModal = useCallback(() => {
    setIsOpen(false);
    setIsLoading(false);
    // Clear config after animation completes
    setTimeout(() => setConfig(null), 300);
  }, []);

  const handleConfirm = useCallback(async () => {
    if (!config?.onConfirm) return;

    try {
      setIsLoading(true);
      await config.onConfirm();
      closeModal();
    } catch (error) {
      console.error("Modal confirmation error:", error);
      setIsLoading(false);
      // Don't close modal on error, let user retry
    }
  }, [config, closeModal]);

  return {
    isOpen,
    config,
    isLoading,
    openModal,
    closeModal,
    handleConfirm,
  };
}
