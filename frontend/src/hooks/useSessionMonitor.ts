"use client";

import { useSession, signOut } from "next-auth/react";
import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

export function useSessionMonitor() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const lastCheckRef = useRef<number>(Date.now());
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Only monitor session if user is authenticated
    if (status === "authenticated" && session) {
      // Check session every minute
      intervalRef.current = setInterval(async () => {
        const now = Date.now();
        const timeSinceLastCheck = now - lastCheckRef.current;
        
        // If it's been more than 5 minutes since last check, verify session
        if (timeSinceLastCheck > 5 * 60 * 1000) {
          try {
            // Try to refresh the session
            const response = await fetch("/api/auth/session");
            const sessionData = await response.json();
            
            // If no session data or expired, logout
            if (!sessionData || !sessionData.user) {
              console.log("Session expired, logging out...");
              sessionStorage.setItem("autoLoggedOut", "true");
              await signOut({ 
                redirect: false,
                callbackUrl: "/auth/signin"
              });
              router.push("/auth/signin");
              return;
            }
          } catch (error) {
            console.error("Session check failed:", error);
            // On error, assume session is invalid and logout
            await signOut({ 
              redirect: false,
              callbackUrl: "/auth/signin"
            });
            router.push("/auth/signin");
            return;
          }
        }
        
        lastCheckRef.current = now;
      }, 60 * 1000); // Check every minute
    }

    // Cleanup interval on unmount or status change
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [status, session, router]);

  // Handle visibility change - check session when user returns to tab
  useEffect(() => {
    const handleVisibilityChange = async () => {
      if (document.visibilityState === "visible" && status === "authenticated") {
        try {
          const response = await fetch("/api/auth/session");
          const sessionData = await response.json();
          
          if (!sessionData || !sessionData.user) {
            console.log("Session expired while tab was inactive, logging out...");
            sessionStorage.setItem("autoLoggedOut", "true");
            await signOut({ 
              redirect: false,
              callbackUrl: "/auth/signin"
            });
            router.push("/auth/signin");
          }
        } catch (error) {
          console.error("Session check on visibility change failed:", error);
        }
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [status, router]);

  return { session, status };
}
