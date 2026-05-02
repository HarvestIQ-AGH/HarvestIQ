"use client"

import { useState, useEffect, useMemo } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Menu, X, Leaf } from "lucide-react"
import { useLanguage } from "@/lib/language-context"
import { LanguageSwitcher } from "@/components/language-switcher"
import { ThemeToggle } from "@/components/theme-toggle"

type NavItem =
  | { kind: "section"; href: string; label: string; id: string }
  | { kind: "page"; href: string; label: string; id: string }

interface HeaderProps {
  activeSection: string
}

export function Header({ activeSection }: HeaderProps) {
  const { t } = useLanguage()
  const pathname = usePathname()
  const [isScrolled, setIsScrolled] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const navItems = useMemo((): NavItem[] => {
    return [
      { kind: "section", href: "#features", label: t.nav.features, id: "features" },
      { kind: "section", href: "#how-it-works", label: t.nav.howItWorks, id: "how-it-works" },
      { kind: "section", href: "#dashboard", label: t.nav.dashboard, id: "dashboard" },
      { kind: "section", href: "#map", label: t.nav.fieldMapping, id: "map" },
      { kind: "page", href: "/pricing", label: t.nav.pricing, id: "pricing" },
      { kind: "section", href: "#waitlist", label: t.nav.joinWaitlist, id: "waitlist" },
    ]
  }, [t])

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20)
    }
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  const scrollToSection = (href: string) => {
    const element = document.querySelector(href)
    if (element) {
      element.scrollIntoView({ behavior: "smooth" })
    }
    setIsMobileMenuOpen(false)
  }

  const itemIsActive = (item: NavItem) => {
    if (item.kind === "page") {
      return pathname === item.href
    }
    return pathname === "/" && activeSection === item.id
  }

  const baseNavClass =
    "px-4 py-2 text-sm font-medium rounded-lg transition-colors block w-full text-left md:inline-block md:w-auto"
  const activeClass = "text-primary bg-primary/10"
  const inactiveClass =
    "text-muted-foreground hover:text-foreground hover:bg-muted"

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? "bg-card/95 backdrop-blur-md shadow-sm border-b border-border"
          : "bg-transparent"
      }`}
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-foreground">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
              <Leaf className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold">HarvestIQ</span>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) =>
              item.kind === "page" ? (
                <Link
                  key={item.id}
                  href={item.href}
                  className={`${baseNavClass} ${itemIsActive(item) ? activeClass : inactiveClass}`}
                >
                  {item.label}
                </Link>
              ) : (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => scrollToSection(item.href)}
                  className={`${baseNavClass} ${itemIsActive(item) ? activeClass : inactiveClass}`}
                >
                  {item.label}
                </button>
              )
            )}
          </nav>

          <div className="hidden md:flex items-center gap-3">
            <ThemeToggle />
            <LanguageSwitcher />
            <Button size="sm" onClick={() => scrollToSection("#waitlist")}>
              {t.common.getEarlyAccess}
            </Button>
          </div>

          <div className="flex md:hidden items-center gap-0.5">
            <ThemeToggle tone="minimal" />
            <LanguageSwitcher tone="minimal" />
            <button
              type="button"
              className="p-2 text-foreground -mr-2"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              aria-label="Toggle menu"
            >
              {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {isMobileMenuOpen && (
        <div className="md:hidden bg-card border-b border-border">
          <div className="px-4 py-4 space-y-2">
            {navItems.map((item) =>
              item.kind === "page" ? (
                <Link
                  key={item.id}
                  href={item.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`${baseNavClass} ${itemIsActive(item) ? activeClass : inactiveClass}`}
                >
                  {item.label}
                </Link>
              ) : (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => scrollToSection(item.href)}
                  className={`${baseNavClass} ${itemIsActive(item) ? activeClass : inactiveClass}`}
                >
                  {item.label}
                </button>
              )
            )}
            <div className="pt-4 border-t border-border">
              <Button className="w-full" onClick={() => scrollToSection("#waitlist")}>
                {t.common.getEarlyAccess}
              </Button>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}
