"use client"

import { useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { ArrowRight, BarChart3, Satellite, CloudSun } from "lucide-react"
import { useLanguage } from "@/lib/language-context"

interface HeroSectionProps {
  onSectionVisible: () => void
}

export function HeroSection({ onSectionVisible }: HeroSectionProps) {
  const { t } = useLanguage()
  const sectionRef = useRef<HTMLElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          onSectionVisible()
        }
      },
      { threshold: 0.5 }
    )

    if (sectionRef.current) {
      observer.observe(sectionRef.current)
    }

    return () => observer.disconnect()
  }, [onSectionVisible])

  const scrollToWaitlist = () => {
    const element = document.querySelector("#waitlist")
    if (element) {
      element.scrollIntoView({ behavior: "smooth" })
    }
  }

  const scrollToMap = () => {
    const element = document.querySelector("#map")
    if (element) {
      element.scrollIntoView({ behavior: "smooth" })
    }
  }

  return (
    <section
      ref={sectionRef}
      id="hero"
      className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16"
    >
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/10 via-background to-background" />

      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent/10 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-8">
            <Satellite className="h-4 w-4" />
            <span>{t.hero.badge}</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground leading-tight text-balance max-w-4xl mx-auto">
            {t.hero.title}
            <span className="text-primary block mt-2">{t.hero.titleLine2}</span>
          </h1>

          <p className="mt-6 text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto text-pretty leading-relaxed">
            {t.hero.description}
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button size="lg" className="w-full sm:w-auto text-base px-8" onClick={scrollToWaitlist}>
              {t.hero.joinWaitlist}
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="w-full sm:w-auto text-base px-8"
              onClick={scrollToMap}
            >
              {t.hero.seeHowItWorks}
            </Button>
          </div>

          <div className="mt-16 grid grid-cols-1 sm:grid-cols-3 gap-8 max-w-3xl mx-auto">
            <div className="flex flex-col items-center gap-3 p-6 rounded-xl bg-card border border-border">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <Satellite className="h-6 w-6 text-primary" />
              </div>
              <div className="text-center">
                <p className="font-semibold text-foreground">{t.hero.satellite}</p>
                <p className="text-sm text-muted-foreground">{t.hero.satelliteDesc}</p>
              </div>
            </div>

            <div className="flex flex-col items-center gap-3 p-6 rounded-xl bg-card border border-border">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <CloudSun className="h-6 w-6 text-primary" />
              </div>
              <div className="text-center">
                <p className="font-semibold text-foreground">{t.hero.weather}</p>
                <p className="text-sm text-muted-foreground">{t.hero.weatherDesc}</p>
              </div>
            </div>

            <div className="flex flex-col items-center gap-3 p-6 rounded-xl bg-card border border-border">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <BarChart3 className="h-6 w-6 text-primary" />
              </div>
              <div className="text-center">
                <p className="font-semibold text-foreground">{t.hero.yield}</p>
                <p className="text-sm text-muted-foreground">{t.hero.yieldDesc}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
