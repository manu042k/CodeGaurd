"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { FaCheckCircle, FaExclamationCircle, FaTimes } from "react-icons/fa";

interface NotificationProps {
  message: string;
  type?: "success" | "error";
  duration?: number;
  onClose: () => void;
}

export function Notification({
  message,
  type = "success",
  duration = 3000,
  onClose,
}: NotificationProps) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(onClose, 300); // Wait for fade out animation
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const getIcon = () => {
    switch (type) {
      case "success":
        return <FaCheckCircle className="h-5 w-5 text-green-600" />;
      case "error":
        return <FaExclamationCircle className="h-5 w-5 text-red-600" />;
      default:
        return <FaCheckCircle className="h-5 w-5 text-green-600" />;
    }
  };

  const getBgColor = () => {
    switch (type) {
      case "success":
        return "bg-green-50 border-green-200";
      case "error":
        return "bg-red-50 border-red-200";
      default:
        return "bg-green-50 border-green-200";
    }
  };

  return createPortal(
    <div
      className={`fixed top-4 right-4 z-50 transition-all duration-300 ${
        isVisible ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-2"
      }`}
    >
      <div
        className={`flex items-center p-4 rounded-lg border shadow-lg max-w-sm ${getBgColor()}`}
      >
        <div className="flex-shrink-0 mr-3">{getIcon()}</div>
        <p className="text-sm font-medium text-gray-900 flex-1">{message}</p>
        <button
          onClick={() => {
            setIsVisible(false);
            setTimeout(onClose, 300);
          }}
          className="ml-3 text-gray-400 hover:text-gray-600"
        >
          <FaTimes className="h-4 w-4" />
        </button>
      </div>
    </div>,
    document.body
  );
}
