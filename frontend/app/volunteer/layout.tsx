import dynamic from "next/dynamic";
import BottomNav from "@/components/BottomNav";

const PwaInstallToast = dynamic(() => import("@/components/PwaInstallToast"), { ssr: false });

export default function VolunteerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <PwaInstallToast />
      <div className="flex-1" style={{ paddingBottom: "calc(4rem + env(safe-area-inset-bottom))" }}>{children}</div>
      <BottomNav />
    </div>
  );
}
