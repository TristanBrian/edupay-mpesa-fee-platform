import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-KE", {
    style: "currency",
    currency: "KES",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat("en-KE", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(date));
}

export function formatDateTime(date: string | Date): string {
  return new Intl.DateTimeFormat("en-KE", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(date));
}

export function formatPercentage(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function getStatusColor(status: string): string {
  const statusColors: Record<string, string> = {
    // Payment statuses
    completed: "text-success",
    paid: "text-success",
    active: "text-success",
    approved: "text-success",
    
    pending: "text-warning",
    pending_approval: "text-warning",
    scheduled: "text-muted-foreground",
    partial: "text-chart-4",
    
    failed: "text-destructive",
    cancelled: "text-destructive",
    overdue: "text-destructive",
    rejected: "text-destructive",
    defaulted: "text-destructive",
    
    // Default
    default: "text-muted-foreground",
  };

  return statusColors[status.toLowerCase()] || statusColors.default;
}

export function getStatusBadgeVariant(status: string): "success" | "warning" | "destructive" | "secondary" {
  const statusVariants: Record<string, "success" | "warning" | "destructive" | "secondary"> = {
    completed: "success",
    paid: "success",
    active: "success",
    approved: "success",
    disbursed: "success",
    
    pending: "warning",
    pending_approval: "warning",
    scheduled: "secondary",
    partial: "warning",
    
    failed: "destructive",
    cancelled: "destructive",
    overdue: "destructive",
    rejected: "destructive",
    defaulted: "destructive",
  };

  return statusVariants[status.toLowerCase()] || "secondary";
}
