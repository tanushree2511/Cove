/**
 * Modern SaaS styled 404 page with glassmorphism card.
 */
import { useLocation, Link } from "react-router-dom";
import { useEffect } from "react";
import { ArrowLeft, FileQuestion } from "lucide-react";
import { motion } from "framer-motion";

const NotFound = () => {
    const location = useLocation();

    useEffect(() => {
        console.error("404 Error: Route not found:", location.pathname);
    }, [location.pathname]);

    return (
        <div className="flex min-h-screen items-center justify-center bg-background p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="max-w-md w-full rounded-2xl border border-border bg-card p-8 text-center shadow-xl"
            >
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary border border-primary/20">
                    <FileQuestion size={28} />
                </div>
                <h1 className="mb-2 text-3xl font-bold text-foreground">404</h1>
                <h2 className="mb-2 text-base font-semibold text-foreground">Page Not Found</h2>
                <p className="mb-6 text-[13px] text-muted-foreground leading-relaxed">
                    The path <code className="rounded bg-muted px-1.5 py-0.5 mono text-[11px] text-foreground">{location.pathname}</code> does not exist in VisionArchive.
                </p>
                <Link
                    to="/"
                    className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-[13px] font-medium text-primary-foreground hover:bg-primary/90 transition-colors shadow-md"
                >
                    <ArrowLeft size={14} /> Back to Library
                </Link>
            </motion.div>
        </div>
    );
};

export default NotFound;
