export const modalStyles = {
  dialog: {
    content: "max-w-4xl max-h-[95vh] bg-[#0F172A] border-[#1E293B] p-0 overflow-hidden flex flex-col",
    header: "p-8 border-b border-[#2D3B4E] flex-shrink-0",
    body: "flex-1 overflow-y-auto p-8",
    footer: "p-8 border-t border-[#2D3B4E] flex-shrink-0"
  },
  inputs: {
    base: "bg-[#1E293B] border-[#2D3B4E]",
    hover: "hover:border-purple-500/20"
  },
  buttons: {
    primary: "bg-emerald-500 hover:bg-emerald-600 text-white",
    secondary: "bg-[#1E293B] border-[#2D3B4E] hover:bg-emerald-500/10 text-slate-200",
    ghost: "text-slate-400 hover:text-emerald-400"
  },
  text: {
    primary: "text-slate-200",
    secondary: "text-slate-400",
    accent: "text-purple-400"
  },
  cards: {
    base: "bg-[#1E293B]/50 hover:bg-[#1E293B] rounded-lg border border-[#1E293B] hover:border-[#7C3AED]/50 transition-all duration-200"
  }
}; 