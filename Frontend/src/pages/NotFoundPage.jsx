import { Link } from "react-router-dom";
import { HelpCircle } from "lucide-react";
import Button from "../components/Button.jsx";

export default function NotFoundPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-12">
      <section className="w-full max-w-[420px] rounded-xl border border-slate-200/80 bg-white p-8 text-center shadow-md animate-in fade-in duration-200">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-blue-50 text-primary shadow-xs">
          <HelpCircle className="h-7 w-7" />
        </div>

        <h1 className="mt-5 text-2xl font-bold text-slate-900 tracking-tight">
          Page Not Found
        </h1>
        <p className="mt-2 text-sm text-slate-500 leading-relaxed">
          The page you are looking for doesn't exist, has been moved, or is
          temporarily unavailable in Campus Pulse.
        </p>

        <div className="mt-8">
          <Link to="/">
            <Button className="w-full font-semibold py-2.5">
              Back to Dashboard
            </Button>
          </Link>
        </div>
      </section>
    </main>
  );
}
