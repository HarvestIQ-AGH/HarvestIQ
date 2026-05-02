"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Check, ChevronDown } from "lucide-react"
import { useLanguage } from "@/lib/language-context"

interface DataInputSectionProps {
  onSectionVisible: () => void
}

const SOIL_KEYS = ["clay", "sandy", "loam", "silt", "peat", "chalky"] as const
type SoilKey = (typeof SOIL_KEYS)[number]

const DATA_CROP_KEYS = ["corn", "soybeans", "wheat", "cotton", "rice", "barley", "oats"] as const
type DataCropKey = (typeof DATA_CROP_KEYS)[number]

const WEATHER_KEYS = ["sunny", "partlyCloudy", "cloudy", "rainy", "stormy"] as const
type WeatherKey = (typeof WEATHER_KEYS)[number]

export function DataInputSection({ onSectionVisible }: DataInputSectionProps) {
  const { t, language } = useLanguage()
  const sectionRef = useRef<HTMLElement>(null)
  const [formData, setFormData] = useState({
    fieldName: "",
    acreage: "",
    soilType: "" as SoilKey | "",
    cropType: "" as DataCropKey | "",
    plantingDate: "",
    soilMoisture: "",
    nitrogenLevel: "",
    phosphorusLevel: "",
    potassiumLevel: "",
    weatherForecast: "" as WeatherKey | "",
    expectedRainfall: "",
  })
  const [openSelect, setOpenSelect] = useState<string | null>(null)
  const [isSubmitted, setIsSubmitted] = useState(false)

  const soilOptions = useMemo(
    () => SOIL_KEYS.map((key) => ({ value: key, label: t.dataInput[key] })),
    [language]
  )

  const cropOptions = useMemo(
    () => DATA_CROP_KEYS.map((key) => ({ value: key, label: t.farmMap[key] })),
    [language]
  )

  const weatherOptions = useMemo(
    () =>
      WEATHER_KEYS.map((key) => ({
        value: key,
        label:
          key === "sunny"
            ? t.dataInput.weatherSunny
            : key === "partlyCloudy"
              ? t.dataInput.weatherPartlyCloudy
              : key === "cloudy"
                ? t.dataInput.weatherCloudy
                : key === "rainy"
                  ? t.dataInput.weatherRainy
                  : t.dataInput.weatherStormy,
      })),
    [language]
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

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleSelectOption = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    setOpenSelect(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitted(true)
    setTimeout(() => setIsSubmitted(false), 3000)
  }

  const SelectDropdown = ({
    field,
    label,
    options,
    placeholder,
  }: {
    field: string
    label: string
    options: { value: string; label: string }[]
    placeholder: string
  }) => {
    const raw = formData[field as keyof typeof formData]
    const selectedLabel =
      typeof raw === "string" && raw
        ? options.find((o) => o.value === raw)?.label ?? raw
        : ""

    return (
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground">{label}</label>
        <div className="relative">
          <button
            type="button"
            onClick={() => setOpenSelect(openSelect === field ? null : field)}
            className="w-full flex items-center justify-between h-9 px-3 rounded-md border border-input bg-transparent text-sm shadow-xs transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <span className={selectedLabel ? "text-foreground" : "text-muted-foreground"}>
              {selectedLabel || placeholder}
            </span>
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          </button>
          {openSelect === field && (
            <div className="absolute z-10 mt-1 w-full rounded-md border border-border bg-card shadow-lg">
              <div className="py-1 max-h-48 overflow-auto">
                {options.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => handleSelectOption(field, option.value)}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-muted transition-colors flex items-center justify-between"
                  >
                    {option.label}
                    {raw === option.value && <Check className="h-4 w-4 text-primary" />}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <section ref={sectionRef} id="data-input" className="py-24 bg-background">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground text-balance">
            {t.dataInput.sectionTitle}
          </h2>
          <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            {t.dataInput.sectionDescription}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>{t.dataInput.fieldInfo}</CardTitle>
              <CardDescription>{t.dataInput.formCardDescription}</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">{t.dataInput.fieldName}</label>
                    <Input
                      placeholder={t.dataInput.fieldNamePlaceholder}
                      value={formData.fieldName}
                      onChange={(e) => handleInputChange("fieldName", e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">{t.dataInput.acreageLabel}</label>
                    <Input
                      type="number"
                      placeholder={t.dataInput.placeholderAcreage}
                      value={formData.acreage}
                      onChange={(e) => handleInputChange("acreage", e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">{t.dataInput.plantingDate}</label>
                    <Input
                      type="date"
                      value={formData.plantingDate}
                      onChange={(e) => handleInputChange("plantingDate", e.target.value)}
                    />
                  </div>

                  <SelectDropdown
                    field="soilType"
                    label={t.dataInput.soilType}
                    options={soilOptions}
                    placeholder={t.dataInput.selectSoilType}
                  />

                  <SelectDropdown
                    field="cropType"
                    label={t.dataInput.cropType}
                    options={cropOptions}
                    placeholder={t.dataInput.selectCrop}
                  />

                  <SelectDropdown
                    field="weatherForecast"
                    label={t.dataInput.currentWeather}
                    options={weatherOptions}
                    placeholder={t.dataInput.selectWeather}
                  />
                </div>

                <div className="border-t border-border pt-8">
                  <h4 className="text-sm font-semibold text-foreground mb-4">{t.dataInput.soilConditions}</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-foreground">{t.dataInput.soilMoisturePct}</label>
                      <Input
                        type="number"
                        placeholder={t.dataInput.placeholderMoisture}
                        min="0"
                        max="100"
                        value={formData.soilMoisture}
                        onChange={(e) => handleInputChange("soilMoisture", e.target.value)}
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium text-foreground">{t.dataInput.nitrogen}</label>
                      <Input
                        type="number"
                        placeholder={t.dataInput.placeholderN}
                        value={formData.nitrogenLevel}
                        onChange={(e) => handleInputChange("nitrogenLevel", e.target.value)}
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium text-foreground">{t.dataInput.phosphorus}</label>
                      <Input
                        type="number"
                        placeholder={t.dataInput.placeholderP}
                        value={formData.phosphorusLevel}
                        onChange={(e) => handleInputChange("phosphorusLevel", e.target.value)}
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium text-foreground">{t.dataInput.potassium}</label>
                      <Input
                        type="number"
                        placeholder={t.dataInput.placeholderK}
                        value={formData.potassiumLevel}
                        onChange={(e) => handleInputChange("potassiumLevel", e.target.value)}
                      />
                    </div>
                  </div>
                </div>

                <div className="border-t border-border pt-8">
                  <h4 className="text-sm font-semibold text-foreground mb-4">{t.dataInput.weatherForecastHeading}</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-foreground">{t.dataInput.expectedRainfall}</label>
                      <Input
                        type="number"
                        placeholder={t.dataInput.placeholderRain}
                        step="0.1"
                        value={formData.expectedRainfall}
                        onChange={(e) => handleInputChange("expectedRainfall", e.target.value)}
                      />
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4">
                  <p className="text-sm text-muted-foreground">{t.dataInput.dataEncrypted}</p>
                  <Button type="submit" size="lg" disabled={isSubmitted}>
                    {isSubmitted ? (
                      <>
                        <Check className="h-5 w-5 mr-2" />
                        {t.dataInput.dataSaved}
                      </>
                    ) : (
                      t.dataInput.saveFieldData
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  )
}
