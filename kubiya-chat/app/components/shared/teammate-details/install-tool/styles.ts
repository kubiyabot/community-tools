import { cn } from "@/lib/utils";

export const styles = {
  animations: {
    slideUp: {
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: 20 },
      transition: { duration: 0.2 }
    }
  },
  dialog: {
    content: "bg-[#0F172A] border border-[#2A3347] p-0 max-w-4xl w-full h-[90vh] overflow-hidden flex flex-col",
    header: "p-6 border-b border-[#2A3347] flex-shrink-0",
    body: "flex-1 flex flex-col min-h-0 overflow-hidden"
  },
  text: {
    primary: "text-slate-200",
    secondary: "text-slate-400",
    accent: "text-purple-400",
    subtitle: "text-sm font-medium text-slate-200 mb-3"
  },
  cards: {
    base: cn(
      "border-slate-800 bg-slate-900/50",
      "dark:border-slate-800 dark:bg-slate-900/50"
    ),
    container: cn(
      "bg-slate-800/50 border border-slate-700",
      "dark:bg-slate-800/50 dark:border-slate-700"
    )
  },
  buttons: {
    ghost: cn(
      "text-slate-400 hover:text-slate-300",
      "hover:bg-slate-800/50"
    ),
    primary: cn(
      "bg-purple-600 text-white",
      "hover:bg-purple-700"
    )
  }
} as const; 