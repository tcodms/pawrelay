"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { isIos, isStandalone } from "@/lib/pwa";

const PwaInstallModal = dynamic(() => import("@/components/PwaInstallModal"), { ssr: false });

const PROMPTED_KEY = "pwa_ios_install_prompted";

function safeGetItem(key: string): string | null {
  try { return localStorage.getItem(key); } catch { return null; }
}

function safeSetItem(key: string, value: string): void {
  try { localStorage.setItem(key, value); } catch {}
}

export default function IosInstallGate() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (!isIos()) return;
    if (isStandalone()) return;
    if (safeGetItem(PROMPTED_KEY)) return;
    setShow(true);
  }, []);

  function handleDismiss() {
    safeSetItem(PROMPTED_KEY, "1");
    setShow(false);
  }

  if (!show) return null;
  return <PwaInstallModal onDismiss={handleDismiss} />;
}
