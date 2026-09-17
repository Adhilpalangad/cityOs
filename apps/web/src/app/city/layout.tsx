import { CityNav } from "@/components/CityNav";

export default function CityLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden">
      <CityNav />
      <main className="flex-1 overflow-y-auto bg-[#060b14]">
        {children}
      </main>
    </div>
  );
}
