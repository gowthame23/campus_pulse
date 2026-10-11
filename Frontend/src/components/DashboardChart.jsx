import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

export default function DashboardChart({
  type = "bar", // 'bar', 'line', or 'donut'
  data = [],
  xKey = "name",
  yKey = "value",
  accentColor = "#2563eb", // Default student blue, typically overridden dynamically
  height = 260,
}) {
  const COLORS = [
    accentColor,
    "#10b981",
    "#f59e0b",
    "#3b82f6",
    "#8b5cf6",
    "#ec4899",
    "#64748b",
  ];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-md text-xs font-semibold text-slate-800">
          <p className="mb-1 text-slate-500 font-bold">{label}</p>
          <p className="flex items-center gap-2">
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{
                backgroundColor: payload[0].payload.fill || accentColor,
              }}
            />
            {payload[0].name}:{" "}
            <span className="font-bold">{payload[0].value}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  const renderChart = () => {
    if (type === "line") {
      return (
        <LineChart
          data={data}
          margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#f1f5f9"
            vertical={false}
          />
          <XAxis
            dataKey={xKey}
            stroke="#94a3b8"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            dy={10}
          />
          <YAxis
            stroke="#94a3b8"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            dx={-10}
            allowDecimals={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey={yKey}
            stroke={accentColor}
            strokeWidth={2.5}
            activeDot={{ r: 6, stroke: "#fff", strokeWidth: 2 }}
            dot={{ r: 3, strokeWidth: 1.5 }}
          />
        </LineChart>
      );
    }

    if (type === "donut") {
      return (
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius="60%"
            outerRadius="80%"
            paddingAngle={3}
            dataKey={yKey}
            nameKey={xKey}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[index % COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip />
          <Legend
            verticalAlign="bottom"
            height={36}
            iconSize={10}
            iconType="circle"
            formatter={(value) => (
              <span className="text-xs font-semibold text-slate-600">
                {value}
              </span>
            )}
          />
        </PieChart>
      );
    }

    // Default: Bar Chart
    return (
      <BarChart
        data={data}
        margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
      >
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="#f1f5f9"
          vertical={false}
        />
        <XAxis
          dataKey={xKey}
          stroke="#94a3b8"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          dy={10}
        />
        <YAxis
          stroke="#94a3b8"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          dx={-10}
          allowDecimals={false}
        />
        <Tooltip content={<CustomTooltip />} />
        <Bar
          dataKey={yKey}
          fill={accentColor}
          radius={[4, 4, 0, 0]}
          maxBarSize={32}
        />
      </BarChart>
    );
  };

  return (
    <div
      style={{ width: "100%", height }}
      className="min-h-[250px] animate-in fade-in duration-200"
    >
      <ResponsiveContainer width="100%" height="100%">
        {renderChart()}
      </ResponsiveContainer>
    </div>
  );
}
