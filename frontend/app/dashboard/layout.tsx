import dynamic from "next/dynamic";
import LogoutButton from "@/components/LogoutButton";

const PwaInstallToast = dynamic(() => import("@/components/PwaInstallToast"), { ssr: false });

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      <PwaInstallToast />
      <LogoutButton />
      {children}
    </div>
  );
}
