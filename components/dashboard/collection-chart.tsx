"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { formatCurrency } from "@/lib/utils";

interface CollectionData {
  period: string;
  invoiced: number;
  collected: number;
}

interface CollectionChartProps {
  data: CollectionData[];
}

export function CollectionChart({ data }: CollectionChartProps) {
  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle>Collection Overview</CardTitle>
        <CardDescription>Invoiced vs collected amounts over time</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={data}
              margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="colorInvoiced" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(var(--chart-3))" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="hsl(var(--chart-3))" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorCollected" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(var(--chart-1))" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="hsl(var(--chart-1))" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="period"
                className="text-xs"
                tick={{ fill: "hsl(var(--muted-foreground))" }}
              />
              <YAxis
                className="text-xs"
                tick={{ fill: "hsl(var(--muted-foreground))" }}
                tickFormatter={(value) => `${(value / 1000).toFixed(0)}K`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "var(--radius)",
                }}
                labelStyle={{ color: "hsl(var(--foreground))" }}
                formatter={(value: number) => [formatCurrency(value), ""]}
              />
              <Area
                type="monotone"
                dataKey="invoiced"
                stroke="hsl(var(--chart-3))"
                fillOpacity={1}
                fill="url(#colorInvoiced)"
                name="Invoiced"
              />
              <Area
                type="monotone"
                dataKey="collected"
                stroke="hsl(var(--chart-1))"
                fillOpacity={1}
                fill="url(#colorCollected)"
                name="Collected"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
