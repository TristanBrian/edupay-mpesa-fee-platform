"use client";

import { Header } from "@/components/layout/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Users, Calendar } from "lucide-react";
import { formatCurrency, formatPercentage } from "@/lib/utils";
import { useState } from "react";

// Demo data for analytics
const collectionTrends = [
  { period: "Jan", invoiced: 850000, collected: 680000, collection_rate: 80 },
  { period: "Feb", invoiced: 920000, collected: 750000, collection_rate: 81.5 },
  { period: "Mar", invoiced: 880000, collected: 720000, collection_rate: 81.8 },
  { period: "Apr", invoiced: 950000, collected: 820000, collection_rate: 86.3 },
  { period: "May", invoiced: 1020000, collected: 890000, collection_rate: 87.3 },
  { period: "Jun", invoiced: 630000, collected: 520000, collection_rate: 82.5 },
];

const paymentMethodDistribution = [
  { name: "M-Pesa STK Push", value: 65, color: "hsl(var(--chart-1))" },
  { name: "M-Pesa C2B", value: 25, color: "hsl(var(--chart-2))" },
  { name: "Bank Transfer", value: 8, color: "hsl(var(--chart-3))" },
  { name: "Cash", value: 2, color: "hsl(var(--chart-4))" },
];

const paymentTimingData = [
  { name: "On-Time", value: 68, count: 234 },
  { name: "1-7 Days Late", value: 18, count: 62 },
  { name: "8-30 Days Late", value: 9, count: 31 },
  { name: "30+ Days Late", value: 5, count: 17 },
];

const schoolPerformance = [
  { name: "Starehe Boys", collected: 2850000, target: 3200000, students: 89 },
  { name: "Alliance Girls", collected: 2420000, target: 2800000, students: 76 },
  { name: "Maseno School", collected: 1980000, target: 2500000, students: 68 },
  { name: "Kenya High", collected: 1650000, target: 1800000, students: 54 },
  { name: "Moi Forces", collected: 1320000, target: 1700000, students: 55 },
];

const predictions = {
  expected_collection_next_30_days: 1250000,
  at_risk_amount: 380000,
  predicted_default_rate: 4.2,
  recommendations: [
    "Send payment reminders to 28 guardians with overdue balances",
    "Consider installment plans for 15 students with high balances",
    "Review credit terms for 5 high-risk accounts",
    "Schedule follow-up calls for accounts 30+ days overdue",
  ],
};

const loanAnalytics = {
  total_disbursed: 2450000,
  total_repaid: 1820000,
  outstanding: 630000,
  default_rate: 3.8,
  average_credit_score: 642,
  approval_rate: 78.5,
};

export default function AnalyticsPage() {
  const [periodFilter, setPeriodFilter] = useState("6months");

  return (
    <div className="flex flex-col">
      <Header
        title="Analytics"
        description="Payment insights and predictive analytics"
      />

      <div className="flex-1 space-y-6 p-6">
        {/* Period Filter */}
        <div className="flex justify-end">
          <Select value={periodFilter} onValueChange={setPeriodFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="30days">Last 30 Days</SelectItem>
              <SelectItem value="3months">Last 3 Months</SelectItem>
              <SelectItem value="6months">Last 6 Months</SelectItem>
              <SelectItem value="1year">Last Year</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Key Metrics */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Collection Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-success" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">82.5%</div>
              <p className="text-xs text-muted-foreground">
                <span className="text-success">+3.2%</span> from last period
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">On-Time Payment Rate</CardTitle>
              <CheckCircle className="h-4 w-4 text-success" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">68%</div>
              <p className="text-xs text-muted-foreground">
                234 of 344 payments on time
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">At-Risk Amount</CardTitle>
              <AlertTriangle className="h-4 w-4 text-warning" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-warning">{formatCurrency(predictions.at_risk_amount)}</div>
              <p className="text-xs text-muted-foreground">
                Likely to default without intervention
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Predicted Collections</CardTitle>
              <Calendar className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(predictions.expected_collection_next_30_days)}</div>
              <p className="text-xs text-muted-foreground">
                Next 30 days forecast
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row 1 */}
        <div className="grid gap-4 lg:grid-cols-3">
          {/* Collection Trends */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Collection Trends</CardTitle>
              <CardDescription>Invoiced vs collected amounts over time</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={collectionTrends}>
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
                    <XAxis dataKey="period" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
                    <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "var(--radius)",
                      }}
                      formatter={(value: number) => [formatCurrency(value), ""]}
                    />
                    <Area type="monotone" dataKey="invoiced" stroke="hsl(var(--chart-3))" fillOpacity={1} fill="url(#colorInvoiced)" name="Invoiced" />
                    <Area type="monotone" dataKey="collected" stroke="hsl(var(--chart-1))" fillOpacity={1} fill="url(#colorCollected)" name="Collected" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Payment Methods */}
          <Card>
            <CardHeader>
              <CardTitle>Payment Methods</CardTitle>
              <CardDescription>Distribution by payment channel</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={paymentMethodDistribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {paymentMethodDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "var(--radius)",
                      }}
                      formatter={(value: number) => [`${value}%`, ""]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 space-y-2">
                {paymentMethodDistribution.map((method, index) => (
                  <div key={index} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full" style={{ backgroundColor: method.color }} />
                      <span>{method.name}</span>
                    </div>
                    <span className="font-medium">{method.value}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row 2 */}
        <div className="grid gap-4 lg:grid-cols-2">
          {/* Payment Timing Analysis */}
          <Card>
            <CardHeader>
              <CardTitle>Payment Timing Analysis</CardTitle>
              <CardDescription>On-time vs late payment distribution</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {paymentTimingData.map((item, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>{item.name}</span>
                      <span className="text-muted-foreground">{item.count} payments ({item.value}%)</span>
                    </div>
                    <Progress 
                      value={item.value} 
                      className={`h-2 ${index === 0 ? '[&>div]:bg-success' : index === 1 ? '[&>div]:bg-warning' : '[&>div]:bg-destructive'}`}
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* School Performance */}
          <Card>
            <CardHeader>
              <CardTitle>School Performance</CardTitle>
              <CardDescription>Collection rate by school</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={schoolPerformance} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis type="number" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`} />
                    <YAxis type="category" dataKey="name" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} width={100} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "var(--radius)",
                      }}
                      formatter={(value: number) => [formatCurrency(value), ""]}
                    />
                    <Bar dataKey="collected" fill="hsl(var(--chart-1))" radius={[0, 4, 4, 0]} name="Collected" />
                    <Bar dataKey="target" fill="hsl(var(--muted))" radius={[0, 4, 4, 0]} name="Target" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Loan Analytics & Predictions */}
        <div className="grid gap-4 lg:grid-cols-2">
          {/* Loan Portfolio */}
          <Card>
            <CardHeader>
              <CardTitle>Loan Portfolio Analytics</CardTitle>
              <CardDescription>Micro-loan performance metrics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-muted-foreground">Total Disbursed</p>
                  <p className="text-2xl font-bold">{formatCurrency(loanAnalytics.total_disbursed)}</p>
                </div>
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-muted-foreground">Total Repaid</p>
                  <p className="text-2xl font-bold text-success">{formatCurrency(loanAnalytics.total_repaid)}</p>
                </div>
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-muted-foreground">Outstanding</p>
                  <p className="text-2xl font-bold text-warning">{formatCurrency(loanAnalytics.outstanding)}</p>
                </div>
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-muted-foreground">Default Rate</p>
                  <p className="text-2xl font-bold text-destructive">{loanAnalytics.default_rate}%</p>
                </div>
              </div>
              <div className="mt-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Avg. Credit Score</span>
                  <span className="font-medium">{loanAnalytics.average_credit_score}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Approval Rate</span>
                  <span className="font-medium">{loanAnalytics.approval_rate}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Repayment Rate</span>
                  <span className="font-medium">{((loanAnalytics.total_repaid / (loanAnalytics.total_repaid + loanAnalytics.outstanding)) * 100).toFixed(1)}%</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* AI Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle>AI-Powered Recommendations</CardTitle>
              <CardDescription>Suggested actions based on payment patterns</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="rounded-lg border bg-muted/50 p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="h-4 w-4 text-primary" />
                    <span className="font-medium">Predicted Default Rate</span>
                  </div>
                  <p className="text-2xl font-bold">{predictions.predicted_default_rate}%</p>
                  <p className="text-xs text-muted-foreground mt-1">Based on current payment patterns</p>
                </div>
                <div className="space-y-3">
                  <p className="text-sm font-medium">Recommended Actions:</p>
                  {predictions.recommendations.map((rec, index) => (
                    <div key={index} className="flex items-start gap-2 text-sm">
                      <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
                      <span className="text-muted-foreground">{rec}</span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
