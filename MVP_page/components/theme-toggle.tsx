"use client"

import { useEffect, useState } from "react"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useLanguage } from "@/lib/language-context"
import { cn } from "@/lib/utils"

type ThemeToggleProps = {
  className?: string
  tone?: "default" | "minimal"
}

export function ThemeToggle({ className, tone = "default" }: ThemeToggleProps) {
  const { t } = useLanguage()
  const { theme, setTheme, resolvedTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const icon =
    !mounted || resolvedTheme === "dark" ? (
      <Moon className="h-[1.15rem] w-[1.15rem]" />
    ) : (
      <Sun className="h-[1.15rem] w-[1.15rem]" />
    )

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className={cn(
            tone === "minimal"
              ? "h-9 w-9 shrink-0 rounded-full border-0 bg-transparent shadow-none hover:bg-muted/60 active:bg-muted"
              : "h-9 w-9 shrink-0 rounded-full border border-border/70 bg-background/90 shadow-sm backdrop-blur-sm hover:bg-muted hover:border-border",
            className
          )}
          aria-label={t.common.theme}
        >
          {icon}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-[10rem]">
        <DropdownMenuRadioGroup value={theme ?? "system"} onValueChange={setTheme}>
          <DropdownMenuRadioItem value="light">{t.common.themeLight}</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="dark">{t.common.themeDark}</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="system">{t.common.themeSystem}</DropdownMenuRadioItem>
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
