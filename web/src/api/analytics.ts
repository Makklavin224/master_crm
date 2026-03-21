import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "./client";

// --- Interfaces (match backend schemas) ---

export interface AnalyticsSummary {
  revenue: number; // kopecks
  booking_count: number;
  client_count: number;
  new_clients: number;
  repeat_clients: number;
  utilization: number; // 0-100%
  avg_check: number; // kopecks
  retention_rate: number; // 0-100%
  cancel_rate: number; // 0-100%
  noshow_rate: number; // 0-100%
}

export interface RevenueChartPoint {
  date: string; // "YYYY-MM-DD"
  revenue: number; // kopecks
}

export interface TopServiceRow {
  service_name: string;
  booking_count: number;
  revenue: number; // kopecks
  percentage: number; // 0-100
}

export interface DailyBreakdownRow {
  date: string; // "YYYY-MM-DD"
  booking_count: number;
  revenue: number; // kopecks
  utilization: number; // 0-100%
}

// --- Params ---

interface AnalyticsParams {
  date_from: string;
  date_to: string;
}

// --- Hooks ---

export function useAnalyticsSummary(params: AnalyticsParams) {
  return useQuery<AnalyticsSummary>({
    queryKey: ["analytics", "summary", params],
    queryFn: () =>
      apiRequest<AnalyticsSummary>(
        `/analytics/summary?date_from=${params.date_from}&date_to=${params.date_to}`,
      ),
    staleTime: 60_000,
  });
}

export function useRevenueChart(params: AnalyticsParams) {
  return useQuery<RevenueChartPoint[]>({
    queryKey: ["analytics", "revenue-chart", params],
    queryFn: () =>
      apiRequest<RevenueChartPoint[]>(
        `/analytics/revenue-chart?date_from=${params.date_from}&date_to=${params.date_to}`,
      ),
    staleTime: 60_000,
  });
}

export function useTopServices(params: AnalyticsParams) {
  return useQuery<TopServiceRow[]>({
    queryKey: ["analytics", "top-services", params],
    queryFn: () =>
      apiRequest<TopServiceRow[]>(
        `/analytics/top-services?date_from=${params.date_from}&date_to=${params.date_to}`,
      ),
    staleTime: 60_000,
  });
}

export function useDailyBreakdown(params: AnalyticsParams) {
  return useQuery<DailyBreakdownRow[]>({
    queryKey: ["analytics", "daily", params],
    queryFn: () =>
      apiRequest<DailyBreakdownRow[]>(
        `/analytics/daily?date_from=${params.date_from}&date_to=${params.date_to}`,
      ),
    staleTime: 60_000,
  });
}

// --- CSV Export ---

export function exportAnalyticsCsv(
  data: DailyBreakdownRow[],
  topServices: TopServiceRow[],
) {
  const BOM = "\uFEFF";
  const lines: string[] = [];

  // Section 1: Top services
  lines.push("Топ услуг");
  lines.push("Услуга,Записей,Доход (руб),% от общего");
  for (const s of topServices) {
    lines.push(
      `"${s.service_name}",${s.booking_count},${(s.revenue / 100).toFixed(2)},${s.percentage.toFixed(1)}%`,
    );
  }

  // Blank line separator
  lines.push("");

  // Section 2: Daily breakdown
  lines.push("По дням");
  lines.push("Дата,Записей,Доход (руб),Загруженность %");
  for (const d of data) {
    lines.push(
      `${d.date},${d.booking_count},${(d.revenue / 100).toFixed(2)},${d.utilization.toFixed(1)}%`,
    );
  }

  const csv = BOM + lines.join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `analytics_${data[0]?.date || "report"}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
