"use client"

import { useLanguage } from "@/lib/language-context"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

type LanguageSwitcherProps = {
  className?: string
  /** `minimal`: flag only, no chrome — for mobile header next to the menu control. */
  tone?: "default" | "minimal"
}

/** Shows the target locale flag: 🇵🇱 when UI is English, 🇺🇸 when UI is Polish. */
export function LanguageSwitcher({ className, tone = "default" }: LanguageSwitcherProps) {
  const { language, setLanguage } = useLanguage()
  const isEn = language === "en"

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      className={cn(
        tone === "minimal"
          ? "h-9 w-9 shrink-0 rounded-full border-0 bg-transparent p-0 text-lg shadow-none hover:bg-muted/60 active:bg-muted"
          : "h-9 w-9 shrink-0 rounded-full border border-border/70 bg-background/90 text-lg shadow-sm backdrop-blur-sm hover:bg-muted hover:border-border",
        className
      )}
      onClick={() => setLanguage(isEn ? "pl" : "en")}
      aria-label={isEn ? "Switch to Polish" : "Switch to English"}
    >
      <span className="pointer-events-none select-none leading-none" aria-hidden>
        {isEn ? "🇵🇱" : "🇺🇸"}
      </span>
    </Button>
  )
}
