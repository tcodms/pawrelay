"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { isIos, isStandalone } from "@/lib/pwa";

const PwaInstallModal = dynamic(() => import("@/components/PwaInstallModal"), { ssr: false });

const PROMPTED_KEY = "pwa_ios_install_prompted";

export default function IosInstallGate() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (!isIos()) return;
    if (isStandalone()) return;
    if (localStorage.getItem(PROMPTED_KEY)) return;
    setShow(true);
  }, []);

  function handleDismiss() {
    localStorage.setItem(PROMPTED_KEY, "1");
    setShow(false);
  }

  if (!show) return null;
  return <PwaInstallModal onDismiss={handleDismiss} />;
}
