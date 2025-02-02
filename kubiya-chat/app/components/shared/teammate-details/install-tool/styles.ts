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
    base: "bg-[#1E293B] border border-[#2D3B4E] rounded-lg",
    container: "bg-[#1E293B] border border-[#2D3B4E] rounded-lg p-4"
  },
  buttons: {
    ghost: "text-slate-400 hover:text-slate-300 hover:bg-[#1E293B]",
    primary: "bg-purple-500 text-white hover:bg-purple-600"
  }
} as const; 