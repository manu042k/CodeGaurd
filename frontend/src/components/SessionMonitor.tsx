"use client";

import { useSessionMonitor } from "@/hooks/useSessionMonitor";

export function SessionMonitor({ children }: { children: React.ReactNode }) {
  // This will automatically monitor the session and handle logout
  useSessionMonitor();
  
  return <>{children}</>;
}
