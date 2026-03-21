import { useState, useMemo } from "react";
import {
  Card,
  Col,
  DatePicker,
  Progress,
  Radio,
  Row,
  Space,
  Spin,
  Statistic,
  Table,
  Tabs,
  Button,
} from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import dayjs, { type Dayjs } from "dayjs";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import {
  useAnalyticsSummary,
  useRevenueChart,
  useTopServices,
  useDailyBreakdown,
  exportAnalyticsCsv,
  type TopServiceRow,
  type DailyBreakdownRow,
} from "../api/analytics";
import type { ColumnsType } from "antd/es/table";

const { RangePicker } = DatePicker;

type PeriodType = "today" | "week" | "month" | "custom";

const PIE_COLORS = ["#6C5CE7", "#00B894"];

function useDateRange(period: PeriodType, customRange: [Dayjs | null, Dayjs | null] | null) {
  return useMemo(() => {
    switch (period) {
      case "today":
        return {
          date_from: dayjs().format("YYYY-MM-DD"),
          date_to: dayjs().format("YYYY-MM-DD"),
        };
      case "week":
        return {
          date_from: dayjs().startOf("week").format("YYYY-MM-DD"),
          date_to: dayjs().endOf("week").format("YYYY-MM-DD"),
        };
      case "month":
        return {
          date_from: dayjs().startOf("month").format("YYYY-MM-DD"),
          date_to: dayjs().endOf("month").format("YYYY-MM-DD"),
        };
      case "custom":
        return {
          date_from: customRange?.[0]?.format("YYYY-MM-DD") ?? dayjs().format("YYYY-MM-DD"),
          date_to: customRange?.[1]?.format("YYYY-MM-DD") ?? dayjs().format("YYYY-MM-DD"),
        };
    }
  }, [period, customRange]);
}

function formatDateTick(value: string) {
  return dayjs(value).format("DD.MM");
}

function formatRubles(value: number) {
  return (value / 100).toLocaleString("ru-RU");
}

// --- Dashboard Tab ---

function DashboardTab({ dateRange }: { dateRange: { date_from: string; date_to: string } }) {
  const { data: summary, isLoading: summaryLoading } = useAnalyticsSummary(dateRange);
  const { data: chartData, isLoading: chartLoading } = useRevenueChart(dateRange);

  if (summaryLoading || chartLoading) {
    return <Spin size="large" style={{ display: "block", margin: "48px auto" }} />;
  }

  if (!summary) return null;

  const pieData = [
    { name: "Новые", value: summary.new_clients },
    { name: "Повторные", value: summary.repeat_clients },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      {/* Top metric cards */}
      <Row gutter={16}>
        <Col span={8}>
          <Card>
            <Statistic
              title="Доход"
              value={summary.revenue / 100}
              suffix="₽"
              formatter={(val) => Number(val).toLocaleString("ru-RU")}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="Записей" value={summary.booking_count} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="Клиентов" value={summary.client_count} />
          </Card>
        </Col>
      </Row>

      {/* Charts row */}
      <Row gutter={16}>
        <Col span={16}>
          <Card title="Динамика дохода">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData ?? []}>
                <XAxis dataKey="date" tickFormatter={formatDateTick} />
                <YAxis tickFormatter={(v) => formatRubles(v)} />
                <Tooltip
                  formatter={(value: number) => [`${formatRubles(value)} ₽`, "Доход"]}
                  labelFormatter={(label: string) => dayjs(label).format("DD.MM.YYYY")}
                />
                <Line
                  type="monotone"
                  dataKey="revenue"
                  stroke="#6C5CE7"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="Новые / Повторные">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={2}
                >
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i]} />
                  ))}
                </Pie>
                <Legend />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Bottom metrics */}
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <div style={{ textAlign: "center" }}>
              <div style={{ marginBottom: 8, color: "rgba(0,0,0,0.45)", fontSize: 14 }}>
                Загруженность
              </div>
              <Progress
                type="dashboard"
                percent={Math.round(summary.utilization)}
                format={(p) => `${p}%`}
                size={100}
              />
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Средний чек"
              value={summary.avg_check / 100}
              suffix="₽"
              formatter={(val) => Number(val).toLocaleString("ru-RU")}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Возвращаемость"
              value={summary.retention_rate.toFixed(1)}
              suffix="%"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Отмены / Неявки"
              value={`${summary.cancel_rate.toFixed(1)}% / ${summary.noshow_rate.toFixed(1)}%`}
            />
          </Card>
        </Col>
      </Row>
    </Space>
  );
}

// --- Reports Tab ---

const topServiceColumns: ColumnsType<TopServiceRow> = [
  {
    title: "Услуга",
    dataIndex: "service_name",
  },
  {
    title: "Записей",
    dataIndex: "booking_count",
    sorter: (a, b) => a.booking_count - b.booking_count,
  },
  {
    title: "Доход",
    dataIndex: "revenue",
    render: (v: number) => `${(v / 100).toLocaleString("ru-RU")} руб`,
    sorter: (a, b) => a.revenue - b.revenue,
  },
  {
    title: "% от общего",
    dataIndex: "percentage",
    render: (v: number) => `${v.toFixed(1)}%`,
    sorter: (a, b) => a.percentage - b.percentage,
  },
];

const dailyColumns: ColumnsType<DailyBreakdownRow> = [
  {
    title: "Дата",
    dataIndex: "date",
    render: (v: string) => dayjs(v).format("DD.MM.YYYY"),
  },
  {
    title: "Записей",
    dataIndex: "booking_count",
    sorter: (a, b) => a.booking_count - b.booking_count,
  },
  {
    title: "Доход",
    dataIndex: "revenue",
    render: (v: number) => `${(v / 100).toLocaleString("ru-RU")} руб`,
    sorter: (a, b) => a.revenue - b.revenue,
  },
  {
    title: "Загруженность",
    dataIndex: "utilization",
    render: (v: number) => `${v.toFixed(1)}%`,
    sorter: (a, b) => a.utilization - b.utilization,
  },
];

function ReportsTab({ dateRange }: { dateRange: { date_from: string; date_to: string } }) {
  const { data: topServices, isLoading: topLoading } = useTopServices(dateRange);
  const { data: daily, isLoading: dailyLoading } = useDailyBreakdown(dateRange);
  const [exporting, setExporting] = useState(false);

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <Button
          icon={<DownloadOutlined />}
          loading={exporting}
          onClick={() => {
            if (!daily || !topServices) return;
            setExporting(true);
            try {
              exportAnalyticsCsv(daily, topServices);
            } finally {
              setExporting(false);
            }
          }}
        >
          Экспорт CSV
        </Button>
      </div>

      <Card title="Топ услуг">
        <Table<TopServiceRow>
          columns={topServiceColumns}
          dataSource={topServices}
          loading={topLoading}
          rowKey="service_name"
          pagination={false}
        />
      </Card>

      <Card title="По дням">
        <Table<DailyBreakdownRow>
          columns={dailyColumns}
          dataSource={daily}
          loading={dailyLoading}
          rowKey="date"
          pagination={{ pageSize: 15, showSizeChanger: false }}
        />
      </Card>
    </Space>
  );
}

// --- Main Page ---

export function AnalyticsPage() {
  const [period, setPeriod] = useState<PeriodType>("month");
  const [customRange, setCustomRange] = useState<[Dayjs | null, Dayjs | null] | null>(null);

  const dateRange = useDateRange(period, customRange);

  return (
    <Card title="Аналитика">
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        {/* Period selector */}
        <Space wrap>
          <Radio.Group
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            optionType="button"
            buttonStyle="solid"
            options={[
              { value: "today", label: "Сегодня" },
              { value: "week", label: "Неделя" },
              { value: "month", label: "Месяц" },
              { value: "custom", label: "Произвольный" },
            ]}
          />
          {period === "custom" && (
            <RangePicker
              format="DD.MM.YYYY"
              value={customRange}
              onChange={(dates) =>
                setCustomRange(dates as [Dayjs | null, Dayjs | null] | null)
              }
              placeholder={["Дата от", "Дата до"]}
            />
          )}
        </Space>

        {/* Tabs */}
        <Tabs
          defaultActiveKey="dashboard"
          items={[
            {
              key: "dashboard",
              label: "Обзор",
              children: <DashboardTab dateRange={dateRange} />,
            },
            {
              key: "reports",
              label: "Отчёты",
              children: <ReportsTab dateRange={dateRange} />,
            },
          ]}
        />
      </Space>
    </Card>
  );
}
