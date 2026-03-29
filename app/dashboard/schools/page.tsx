"use client";

import { useState } from "react";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { DataTable } from "@/components/ui/data-table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Search, School, Users, DollarSign } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

interface SchoolData {
  id: number;
  name: string;
  code: string;
  email: string;
  phone: string;
  address: string;
  mpesa_shortcode: string;
  students: number;
  total_fees: number;
  collected: number;
  status: string;
}

// Demo data
const demoSchools: SchoolData[] = [
  { id: 1, name: "Starehe Boys Centre", code: "SBC", email: "admin@starehe.ac.ke", phone: "+254712345678", address: "Nairobi, Kenya", mpesa_shortcode: "174379", students: 89, total_fees: 6675000, collected: 5340000, status: "active" },
  { id: 2, name: "Alliance Girls High School", code: "AGHS", email: "admin@alliance.ac.ke", phone: "+254723456789", address: "Kikuyu, Kenya", mpesa_shortcode: "174380", students: 76, total_fees: 4940000, collected: 4200000, status: "active" },
  { id: 3, name: "Maseno School", code: "MAS", email: "admin@maseno.ac.ke", phone: "+254734567890", address: "Maseno, Kenya", mpesa_shortcode: "174381", students: 68, total_fees: 5440000, collected: 3808000, status: "active" },
  { id: 4, name: "Kenya High School", code: "KHS", email: "admin@kenyahigh.ac.ke", phone: "+254745678901", address: "Nairobi, Kenya", mpesa_shortcode: "174382", students: 54, total_fees: 3780000, collected: 3402000, status: "active" },
  { id: 5, name: "Moi Forces Academy", code: "MFA", email: "admin@moiforces.ac.ke", phone: "+254756789012", address: "Nairobi, Kenya", mpesa_shortcode: "174383", students: 55, total_fees: 3960000, collected: 2772000, status: "active" },
];

const columns = [
  {
    key: "name",
    header: "School",
    cell: (school: SchoolData) => (
      <div>
        <p className="font-medium">{school.name}</p>
        <p className="text-xs text-muted-foreground">Code: {school.code}</p>
      </div>
    ),
  },
  {
    key: "contact",
    header: "Contact",
    cell: (school: SchoolData) => (
      <div>
        <p className="text-sm">{school.email}</p>
        <p className="text-xs text-muted-foreground">{school.phone}</p>
      </div>
    ),
  },
  {
    key: "mpesa",
    header: "M-Pesa Shortcode",
    cell: (school: SchoolData) => (
      <span className="font-mono text-sm">{school.mpesa_shortcode}</span>
    ),
  },
  {
    key: "students",
    header: "Students",
    cell: (school: SchoolData) => (
      <span className="font-medium">{school.students}</span>
    ),
  },
  {
    key: "fees",
    header: "Fees Collection",
    cell: (school: SchoolData) => (
      <div>
        <p className="font-medium">{formatCurrency(school.collected)}</p>
        <p className="text-xs text-muted-foreground">
          of {formatCurrency(school.total_fees)} ({((school.collected / school.total_fees) * 100).toFixed(1)}%)
        </p>
      </div>
    ),
  },
  {
    key: "status",
    header: "Status",
    cell: (school: SchoolData) => (
      <Badge variant="success">{school.status}</Badge>
    ),
  },
];

export default function SchoolsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);

  const filteredSchools = demoSchools.filter((school) =>
    school.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    school.code.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalStudents = demoSchools.reduce((sum, s) => sum + s.students, 0);
  const totalFees = demoSchools.reduce((sum, s) => sum + s.total_fees, 0);
  const totalCollected = demoSchools.reduce((sum, s) => sum + s.collected, 0);

  return (
    <div className="flex flex-col">
      <Header
        title="Schools"
        description="Manage registered schools"
      />

      <div className="flex-1 space-y-4 p-6">
        {/* Summary Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Schools</CardTitle>
              <School className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{demoSchools.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Students</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalStudents}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Fees</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(totalFees)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Collection Rate</CardTitle>
              <DollarSign className="h-4 w-4 text-success" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-success">
                {((totalCollected / totalFees) * 100).toFixed(1)}%
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters and Actions */}
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search schools..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>

          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add School
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Add New School</DialogTitle>
                <DialogDescription>
                  Register a new school in the system.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="schoolName">School Name</Label>
                    <Input id="schoolName" placeholder="Starehe Boys Centre" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="schoolCode">School Code</Label>
                    <Input id="schoolCode" placeholder="SBC" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="schoolEmail">Email</Label>
                    <Input id="schoolEmail" type="email" placeholder="admin@school.ac.ke" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="schoolPhone">Phone</Label>
                    <Input id="schoolPhone" placeholder="+254712345678" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="schoolAddress">Address</Label>
                  <Input id="schoolAddress" placeholder="Nairobi, Kenya" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="mpesaShortcode">M-Pesa Shortcode</Label>
                  <Input id="mpesaShortcode" placeholder="174379" />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={() => setIsAddDialogOpen(false)}>
                  Add School
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {/* Data Table */}
        <DataTable
          columns={columns}
          data={filteredSchools}
          keyExtractor={(school) => school.id}
          emptyMessage="No schools found"
        />
      </div>
    </div>
  );
}
