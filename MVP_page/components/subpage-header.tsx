"use client"

import Link from "next/link"
import { Leaf } from "lucide-react"
import { useLanguage } from "@/lib/language-context"
import { LanguageSwitcher } from "@/components/language-switcher"
import { ThemeToggle } from "@/components/theme-toggle"

export function SubpageHeader() {
  const { t } = useLanguage()

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-card/95 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <Link
          href="/"
          className="flex min-w-0 items-center gap-2 text-foreground transition-opacity hover:opacity-90"
        >
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary">
            <Leaf className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="text-xl font-bold">HarvestIQ</span>
        </Link>
        <div className="flex items-center gap-3 shrink-0">
          <ThemeToggle />
          <LanguageSwitcher />
          <Link
            href="/"
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground whitespace-nowrap"
          >
            {t.common.backToHome}
          </Link>
        </div>
      </div>
    </header>
  )
}
