"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatCurrency, formatDateTime, getStatusBadgeVariant } from "@/lib/utils";

interface Payment {
  id: number;
  payment_reference: string;
  amount: number;
  status: string;
  created_at: string;
  student_name?: string;
}

interface RecentPaymentsProps {
  payments: Payment[];
}

export function RecentPayments({ payments }: RecentPaymentsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Payments</CardTitle>
        <CardDescription>Latest M-Pesa transactions</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {payments.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              No recent payments
            </p>
          ) : (
            payments.map((payment) => (
              <div
                key={payment.id}
                className="flex items-center justify-between"
              >
                <div className="space-y-1">
                  <p className="text-sm font-medium leading-none">
                    {payment.payment_reference}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {payment.student_name || formatDateTime(payment.created_at)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={getStatusBadgeVariant(payment.status)}>
                    {payment.status}
                  </Badge>
                  <span className="text-sm font-medium">
                    {formatCurrency(payment.amount)}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
