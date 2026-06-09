"use client";

import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

type StatusAnnouncerContextValue = {
  politeMessage: string;
  assertiveMessage: string;
  announcePolite: (message: string) => void;
  announceAssertive: (message: string) => void;
};

const StatusAnnouncerContext = createContext<StatusAnnouncerContextValue | null>(
  null,
);

export function StatusAnnouncerProvider({ children }: { children: ReactNode }) {
  const [politeMessage, setPoliteMessage] = useState("");
  const [assertiveMessage, setAssertiveMessage] = useState("");

  const announcePolite = useCallback((message: string) => {
    setPoliteMessage("");
    requestAnimationFrame(() => setPoliteMessage(message));
  }, []);

  const announceAssertive = useCallback((message: string) => {
    setAssertiveMessage("");
    requestAnimationFrame(() => setAssertiveMessage(message));
  }, []);

  return (
    <StatusAnnouncerContext.Provider
      value={{ politeMessage, assertiveMessage, announcePolite, announceAssertive }}
    >
      {children}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {politeMessage}
      </div>
      <div
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
        className="sr-only"
      >
        {assertiveMessage}
      </div>
    </StatusAnnouncerContext.Provider>
  );
}

export function useStatusAnnouncer(): StatusAnnouncerContextValue {
  const ctx = useContext(StatusAnnouncerContext);
  if (!ctx) {
    throw new Error("useStatusAnnouncer must be used within StatusAnnouncerProvider");
  }
  return ctx;
}
