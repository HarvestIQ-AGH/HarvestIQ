"use client"

import { useEffect, useRef } from "react"
import { useLanguage } from "@/lib/language-context"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, Droplets, Sun, Wheat } from "lucide-react"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
} from "recharts"

interface DashboardPreviewProps {
  onSectionVisible: () => void
}

const yieldData = [
  { month: "Jan", actual: 0, predicted: 0 },
  { month: "Feb", actual: 0, predicted: 0 },
  { month: "Mar", actual: 12, predicted: 15 },
  { month: "Apr", actual: 28, predicted: 32 },
  { month: "May", actual: 45, predicted: 48 },
  { month: "Jun", actual: 62, predicted: 65 },
  { month: "Jul", actual: 78, predicted: 82 },
  { month: "Aug", actual: 88, predicted: 92 },
  { month: "Sep", actual: 95, predicted: 98 },
]

const moistureData = [
  { day: "Mon", level: 65 },
  { day: "Tue", level: 58 },
  { day: "Wed", level: 72 },
  { day: "Thu", level: 68 },
  { day: "Fri", level: 45 },
  { day: "Sat", level: 52 },
  { day: "Sun", level: 61 },
]

const cropHealthData = [
  { field: "North", health: 92 },
  { field: "South", health: 78 },
  { field: "East", health: 85 },
  { field: "West", health: 88 },
]

export function DashboardPreview({ onSectionVisible }: DashboardPreviewProps) {
  const { t } = useLanguage()
  const sectionRef = useRef<HTMLElement>(null)

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
    <section ref={sectionRef} id="dashboard" className="py-24 bg-muted/30">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground text-balance">
            {t.dashboard.title}
          </h2>
          <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            {t.dashboard.previewSubtitle}
          </p>
        </div>

        <div className="p-4 sm:p-8 rounded-2xl bg-card border border-border shadow-xl">
          <div className="mb-6 flex items-center justify-between border-b border-border pb-4">
            <div>
              <h3 className="text-lg font-semibold text-foreground">{t.dashboard.farmDashboard}</h3>
              <p className="text-sm text-muted-foreground">{t.dashboard.lastUpdated}</p>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary text-sm font-medium">
              <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
              {t.dashboard.live}
            </div>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <Card className="border-0 shadow-none bg-muted/50">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-chart-1/20">
                    <Wheat className="h-5 w-5 text-chart-1" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">{t.dashboard.yieldForecast}</p>
                    <p className="text-xl font-bold text-foreground">98 bu/ac</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-none bg-muted/50">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-chart-3/20">
                    <Droplets className="h-5 w-5 text-chart-3" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">{t.dashboard.moistureShort}</p>
                    <p className="text-xl font-bold text-foreground">61%</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-none bg-muted/50">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-chart-4/20">
                    <Sun className="h-5 w-5 text-chart-4" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">{t.dashboard.gddTotal}</p>
                    <p className="text-xl font-bold text-foreground">2,450</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-none bg-muted/50">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/20">
                    <TrendingUp className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">{t.dashboard.cropHealthShort}</p>
                    <p className="text-xl font-bold text-foreground">86%</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-medium">{t.dashboard.yieldProjection}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={yieldData}>
                      <defs>
                        <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="oklch(0.55 0.15 145)" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="oklch(0.55 0.15 145)" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.9 0.02 90)" />
                      <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="oklch(0.5 0.02 60)" />
                      <YAxis tick={{ fontSize: 12 }} stroke="oklch(0.5 0.02 60)" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "oklch(1 0 0)",
                          border: "1px solid oklch(0.9 0.02 90)",
                          borderRadius: "8px",
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="predicted"
                        stroke="oklch(0.55 0.15 145)"
                        fillOpacity={1}
                        fill="url(#colorPredicted)"
                        strokeWidth={2}
                      />
                      <Line
                        type="monotone"
                        dataKey="actual"
                        stroke="oklch(0.65 0.12 85)"
                        strokeWidth={2}
                        dot={{ fill: "oklch(0.65 0.12 85)", strokeWidth: 0 }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex items-center justify-center gap-6 mt-4">
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full bg-primary" />
                    <span className="text-sm text-muted-foreground">{t.dashboard.chartPredicted}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full bg-accent" />
                    <span className="text-sm text-muted-foreground">{t.dashboard.chartActual}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="space-y-6">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base font-medium">{t.dashboard.soilMoisture7d}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-28">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={moistureData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.9 0.02 90)" />
                        <XAxis dataKey="day" tick={{ fontSize: 11 }} stroke="oklch(0.5 0.02 60)" />
                        <YAxis tick={{ fontSize: 11 }} stroke="oklch(0.5 0.02 60)" domain={[0, 100]} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "oklch(1 0 0)",
                            border: "1px solid oklch(0.9 0.02 90)",
                            borderRadius: "8px",
                          }}
                        />
                        <Line
                          type="monotone"
                          dataKey="level"
                          stroke="oklch(0.45 0.1 200)"
                          strokeWidth={2}
                          dot={{ fill: "oklch(0.45 0.1 200)", strokeWidth: 0, r: 3 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base font-medium">{t.dashboard.fieldHealth}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-28">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={cropHealthData} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.9 0.02 90)" />
                        <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} stroke="oklch(0.5 0.02 60)" />
                        <YAxis type="category" dataKey="field" tick={{ fontSize: 11 }} stroke="oklch(0.5 0.02 60)" width={50} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "oklch(1 0 0)",
                            border: "1px solid oklch(0.9 0.02 90)",
                            borderRadius: "8px",
                          }}
                        />
                        <Bar dataKey="health" fill="oklch(0.55 0.15 145)" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
