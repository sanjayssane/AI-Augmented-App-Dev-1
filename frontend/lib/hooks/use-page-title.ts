"use client";

import { useEffect } from "react";

const APP_NAME = "MCQ Test Platform";

export function usePageTitle(title: string): void {
  useEffect(() => {
    document.title = `${title} – ${APP_NAME}`;
  }, [title]);
}
