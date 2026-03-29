"use client";

import { Header } from "@/components/layout/header";
import { StatsCard } from "@/components/dashboard/stats-card";
import { CollectionChart } from "@/components/dashboard/collection-chart";
import { RecentPayments } from "@/components/dashboard/recent-payments";
import { AtRiskStudents } from "@/components/dashboard/at-risk-students";
import {
  DollarSign,
  Users,
  CreditCard,
  TrendingUp,
  Wallet,
  AlertTriangle,
} from "lucide-react";
import { formatCurrency, formatPercentage } from "@/lib/utils";

// Demo data for testing without backend
const demoAnalytics = {
  total_invoiced: 5250000,
  total_collected: 4125000,
  total_outstanding: 1125000,
  collection_rate: 78.5,
  total_students: 342,
  paying_students: 289,
  active_installment_plans: 45,
  active_loans: 23,
  on_time_payment_rate: 82.3,
  overdue_count: 28,
};

const demoTrends = [
  { period: "Jan", invoiced: 850000, collected: 680000 },
  { period: "Feb", invoiced: 920000, collected: 750000 },
  { period: "Mar", invoiced: 880000, collected: 720000 },
  { period: "Apr", invoiced: 950000, collected: 820000 },
  { period: "May", invoiced: 1020000, collected: 890000 },
  { period: "Jun", invoiced: 630000, collected: 265000 },
];

const demoPayments = [
  { id: 1, payment_reference: "PAY-2024-001", amount: 45000, status: "completed", created_at: "2024-03-15T10:30:00", student_name: "John Kamau" },
  { id: 2, payment_reference: "PAY-2024-002", amount: 32000, status: "completed", created_at: "2024-03-15T09:45:00", student_name: "Mary Wanjiku" },
  { id: 3, payment_reference: "PAY-2024-003", amount: 15000, status: "pending", created_at: "2024-03-15T09:15:00", student_name: "Peter Ochieng" },
  { id: 4, payment_reference: "PAY-2024-004", amount: 28000, status: "completed", created_at: "2024-03-14T16:20:00", student_name: "Grace Muthoni" },
  { id: 5, payment_reference: "PAY-2024-005", amount: 50000, status: "failed", created_at: "2024-03-14T14:00:00", student_name: "David Kiprop" },
];

const demoAtRiskStudents = [
  { student_id: 1, student_name: "James Mwangi", admission_number: "ADM-001", outstanding_amount: 75000, days_overdue: 45, risk_score: 85, guardian_phone: "+254712345678" },
  { student_id: 2, student_name: "Faith Akinyi", admission_number: "ADM-002", outstanding_amount: 52000, days_overdue: 30, risk_score: 65, guardian_phone: "+254723456789" },
  { student_id: 3, student_name: "Samuel Otieno", admission_number: "ADM-003", outstanding_amount: 38000, days_overdue: 21, risk_score: 45, guardian_phone: "+254734567890" },
  { student_id: 4, student_name: "Lucy Wambui", admission_number: "ADM-004", outstanding_amount: 25000, days_overdue: 14, risk_score: 30, guardian_phone: "+254745678901" },
];

export default function DashboardPage() {
  const analytics = demoAnalytics;
  const trends = demoTrends;
  const payments = demoPayments;
  const atRiskStudents = demoAtRiskStudents;

  return (
    <div className="flex flex-col">
      <Header
        title="Dashboard"
        description="Overview of your school fee management"
      />

      <div className="flex-1 space-y-6 p-6">
        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          <StatsCard
            title="Total Invoiced"
            value={formatCurrency(analytics.total_invoiced)}
            description="This term"
            icon={DollarSign}
          />
          <StatsCard
            title="Total Collected"
            value={formatCurrency(analytics.total_collected)}
            description="This term"
            icon={CreditCard}
            trend={{ value: 12.5, isPositive: true }}
          />
          <StatsCard
            title="Outstanding"
            value={formatCurrency(analytics.total_outstanding)}
            description={`${analytics.overdue_count} overdue`}
            icon={AlertTriangle}
          />
          <StatsCard
            title="Collection Rate"
            value={formatPercentage(analytics.collection_rate)}
            description="vs last month"
            icon={TrendingUp}
            trend={{ value: 3.2, isPositive: true }}
          />
          <StatsCard
            title="Active Students"
            value={analytics.total_students}
            description={`${analytics.paying_students} paying`}
            icon={Users}
          />
          <StatsCard
            title="Active Plans"
            value={analytics.active_installment_plans + analytics.active_loans}
            description={`${analytics.active_installment_plans} installments, ${analytics.active_loans} loans`}
            icon={Wallet}
          />
        </div>

        {/* Charts and Recent Activity */}
        <div className="grid gap-4 lg:grid-cols-3">
          <CollectionChart data={trends} />
          <RecentPayments payments={payments} />
        </div>

        {/* At-Risk Students */}
        <div className="grid gap-4 lg:grid-cols-2">
          <AtRiskStudents students={atRiskStudents} />
          
          {/* Quick Actions Card */}
          <div className="rounded-lg border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
            <div className="grid grid-cols-2 gap-3">
              <a
                href="/dashboard/students"
                className="flex flex-col items-center justify-center gap-2 rounded-lg border bg-background p-4 text-center hover:bg-accent transition-colors"
              >
                <Users className="h-6 w-6 text-primary" />
                <span className="text-sm font-medium">Add Student</span>
              </a>
              <a
                href="/dashboard/invoices"
                className="flex flex-col items-center justify-center gap-2 rounded-lg border bg-background p-4 text-center hover:bg-accent transition-colors"
              >
                <DollarSign className="h-6 w-6 text-primary" />
                <span className="text-sm font-medium">Create Invoice</span>
              </a>
              <a
                href="/dashboard/payments"
                className="flex flex-col items-center justify-center gap-2 rounded-lg border bg-background p-4 text-center hover:bg-accent transition-colors"
              >
                <CreditCard className="h-6 w-6 text-primary" />
                <span className="text-sm font-medium">Record Payment</span>
              </a>
              <a
                href="/dashboard/installments"
                className="flex flex-col items-center justify-center gap-2 rounded-lg border bg-background p-4 text-center hover:bg-accent transition-colors"
              >
                <Wallet className="h-6 w-6 text-primary" />
                <span className="text-sm font-medium">Setup Plan</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
