"use client"

import Link from "next/link"
import { Leaf } from "lucide-react"
import { useLanguage } from "@/lib/language-context"

const linkClass =
  "inline-block text-sm text-muted-foreground hover:text-foreground transition-colors text-left"

export function Footer() {
  const { t } = useLanguage()

  const productLinks = [
    { label: t.footer.features, href: "/#features" },
    { label: t.footer.howItWorks, href: "/#how-it-works" },
    { label: t.footer.dashboard, href: "/#dashboard" },
    { label: t.footer.pricing, href: "/pricing" },
  ]

  const companyLinks = [
    { label: t.footer.about, href: "/about" },
    { label: t.footer.contact, href: "/contact" },
  ]

  return (
    <footer className="bg-card border-t border-border">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-3 gap-8">
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="inline-flex items-center gap-2 mb-4 text-foreground">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
                <Leaf className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold">HarvestIQ</span>
            </Link>
            <p className="text-sm text-muted-foreground leading-relaxed max-w-xs">
              {t.footer.description}
            </p>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-foreground mb-4">{t.footer.product}</h3>
            <ul className="space-y-3">
              {productLinks.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className={linkClass}>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-foreground mb-4">{t.footer.company}</h3>
            <ul className="space-y-3">
              {companyLinks.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className={linkClass}>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-border">
          <p className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} HarvestIQ. {t.footer.rightsReserved}
          </p>
        </div>
      </div>
    </footer>
  )
}
