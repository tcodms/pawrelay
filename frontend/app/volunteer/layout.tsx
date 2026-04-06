import BottomNav from "@/components/BottomNav";

export default function VolunteerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <div className="flex-1 pb-16">{children}</div>
      <BottomNav />
    </div>
  );
}
