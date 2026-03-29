"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Phone } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

interface AtRiskStudent {
  student_id: number;
  student_name: string;
  admission_number: string;
  outstanding_amount: number;
  days_overdue: number;
  risk_score: number;
  guardian_phone: string;
}

interface AtRiskStudentsProps {
  students: AtRiskStudent[];
}

function getRiskLevel(score: number): { label: string; variant: "destructive" | "warning" | "secondary" } {
  if (score >= 80) return { label: "High Risk", variant: "destructive" };
  if (score >= 50) return { label: "Medium Risk", variant: "warning" };
  return { label: "Low Risk", variant: "secondary" };
}

export function AtRiskStudents({ students }: AtRiskStudentsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>At-Risk Students</CardTitle>
        <CardDescription>Students with overdue payments requiring attention</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {students.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              No at-risk students
            </p>
          ) : (
            students.slice(0, 5).map((student) => {
              const risk = getRiskLevel(student.risk_score);
              return (
                <div
                  key={student.student_id}
                  className="flex items-center justify-between gap-4"
                >
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium leading-none">
                        {student.student_name}
                      </p>
                      <Badge variant={risk.variant} className="text-[10px]">
                        {risk.label}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {student.admission_number} - {student.days_overdue} days overdue
                    </p>
                    <div className="flex items-center gap-2">
                      <Progress value={student.risk_score} className="h-1.5 flex-1" />
                      <span className="text-xs text-muted-foreground">{student.risk_score}%</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {formatCurrency(student.outstanding_amount)}
                    </p>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 text-xs"
                      asChild
                    >
                      <a href={`tel:${student.guardian_phone}`}>
                        <Phone className="h-3 w-3 mr-1" />
                        Call
                      </a>
                    </Button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </CardContent>
    </Card>
  );
}
