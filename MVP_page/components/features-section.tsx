"use client"

import { useEffect, useRef, useMemo } from "react"
import { Card, CardContent } from "@/components/ui/card"
import {
  BarChart3,
  Bell,
  CloudSun,
  Database,
  LineChart,
  Lock,
  Map,
  Sprout,
  TrendingUp,
} from "lucide-react"
import { useLanguage } from "@/lib/language-context"
import type { Translations } from "@/lib/translations"

interface FeaturesSectionProps {
  onSectionVisible: () => void
}

type FeatureKey =
  | "yieldPrediction"
  | "fieldMapping"
  | "weatherIntelligence"
  | "smartAlerts"
  | "cropHealth"
  | "inputOptimization"
  | "historicalAnalytics"
  | "dataTraceability"
  | "secureAccess"

const FEATURE_ROWS: { icon: typeof BarChart3; key: FeatureKey }[] = [
  { icon: BarChart3, key: "yieldPrediction" },
  { icon: Map, key: "fieldMapping" },
  { icon: CloudSun, key: "weatherIntelligence" },
  { icon: Bell, key: "smartAlerts" },
  { icon: Sprout, key: "cropHealth" },
  { icon: TrendingUp, key: "inputOptimization" },
  { icon: LineChart, key: "historicalAnalytics" },
  { icon: Database, key: "dataTraceability" },
  { icon: Lock, key: "secureAccess" },
]

function featureDesc(t: Translations["features"], key: FeatureKey): string {
  const map: Record<FeatureKey, keyof Translations["features"]> = {
    yieldPrediction: "yieldPredictionDesc",
    fieldMapping: "fieldMappingDesc",
    weatherIntelligence: "weatherIntelligenceDesc",
    smartAlerts: "smartAlertsDesc",
    cropHealth: "cropHealthDesc",
    inputOptimization: "inputOptimizationDesc",
    historicalAnalytics: "historicalAnalyticsDesc",
    dataTraceability: "dataTraceabilityDesc",
    secureAccess: "secureAccessDesc",
  }
  return t[map[key]] as string
}

export function FeaturesSection({ onSectionVisible }: FeaturesSectionProps) {
  const { t } = useLanguage()
  const sectionRef = useRef<HTMLElement>(null)

  const features = useMemo(
    () =>
      FEATURE_ROWS.map(({ icon, key }) => ({
        icon,
        title: t.features[key],
        description: featureDesc(t.features, key),
      })),
    [t]
  )

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          onSectionVisible()
        }
      },
      { threshold: 0.3 }
    )

    if (sectionRef.current) {
      observer.observe(sectionRef.current)
    }

    return () => observer.disconnect()
  }, [onSectionVisible])

  return (
    <section ref={sectionRef} id="features" className="py-24 bg-muted/30">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground text-balance">
            {t.features.sectionTitle}
          </h2>
          <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            {t.features.sectionDescription}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <Card
              key={feature.title}
              className="group hover:shadow-lg transition-all duration-300 hover:border-primary/30"
            >
              <CardContent className="pt-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 group-hover:bg-primary/20 transition-colors">
                  <feature.icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-foreground">{feature.title}</h3>
                <p className="mt-2 text-muted-foreground text-sm leading-relaxed">
                  {feature.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
