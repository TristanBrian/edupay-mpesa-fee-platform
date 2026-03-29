"use client";

import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Shield, Key, Bell, Database, Smartphone, CheckCircle } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="flex flex-col">
      <Header
        title="Settings"
        description="Configure system and M-Pesa integration"
      />

      <div className="flex-1 p-6">
        <Tabs defaultValue="mpesa" className="space-y-6">
          <TabsList>
            <TabsTrigger value="mpesa">M-Pesa Integration</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="security">Security</TabsTrigger>
            <TabsTrigger value="system">System</TabsTrigger>
          </TabsList>

          <TabsContent value="mpesa" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Smartphone className="h-5 w-5" />
                      M-Pesa Daraja API
                    </CardTitle>
                    <CardDescription>
                      Configure your Safaricom M-Pesa integration credentials
                    </CardDescription>
                  </div>
                  <Badge variant="success" className="flex items-center gap-1">
                    <CheckCircle className="h-3 w-3" />
                    Connected
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="consumerKey">Consumer Key</Label>
                    <Input id="consumerKey" type="password" value="••••••••••••••••" readOnly />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="consumerSecret">Consumer Secret</Label>
                    <Input id="consumerSecret" type="password" value="••••••••••••••••" readOnly />
                  </div>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="shortcode">Business Shortcode</Label>
                    <Input id="shortcode" value="174379" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="passkey">Passkey</Label>
                    <Input id="passkey" type="password" value="••••••••••••••••" readOnly />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="callbackUrl">Callback URL</Label>
                  <Input id="callbackUrl" value="https://api.edupay.co.ke/api/v1/payments/callback" />
                </div>
                <div className="space-y-2">
                  <Label>Environment</Label>
                  <Select defaultValue="sandbox">
                    <SelectTrigger className="w-[200px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sandbox">Sandbox (Testing)</SelectItem>
                      <SelectItem value="production">Production</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline">Test Connection</Button>
                  <Button>Save Changes</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="notifications" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5" />
                  SMS Notifications
                </CardTitle>
                <CardDescription>
                  Configure automated SMS reminders and alerts
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-4">
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">Payment Confirmation</p>
                      <p className="text-sm text-muted-foreground">Send SMS when payment is received</p>
                    </div>
                    <Badge variant="success">Enabled</Badge>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">Payment Reminders</p>
                      <p className="text-sm text-muted-foreground">Send reminders before due date</p>
                    </div>
                    <Badge variant="success">Enabled</Badge>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">Overdue Alerts</p>
                      <p className="text-sm text-muted-foreground">Send alerts for overdue payments</p>
                    </div>
                    <Badge variant="success">Enabled</Badge>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">Installment Due Reminders</p>
                      <p className="text-sm text-muted-foreground">Remind guardians of upcoming installments</p>
                    </div>
                    <Badge variant="success">Enabled</Badge>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Reminder Days Before Due</Label>
                  <Select defaultValue="3">
                    <SelectTrigger className="w-[200px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1 day</SelectItem>
                      <SelectItem value="3">3 days</SelectItem>
                      <SelectItem value="7">7 days</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="security" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Security Settings
                </CardTitle>
                <CardDescription>
                  Configure security and access controls
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-4">
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">Rate Limiting</p>
                      <p className="text-sm text-muted-foreground">Limit API requests per minute</p>
                    </div>
                    <Select defaultValue="100">
                      <SelectTrigger className="w-[120px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="50">50/min</SelectItem>
                        <SelectItem value="100">100/min</SelectItem>
                        <SelectItem value="200">200/min</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">IP Whitelisting</p>
                      <p className="text-sm text-muted-foreground">Restrict API access to specific IPs</p>
                    </div>
                    <Badge variant="secondary">Disabled</Badge>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">Audit Logging</p>
                      <p className="text-sm text-muted-foreground">Log all API requests and actions</p>
                    </div>
                    <Badge variant="success">Enabled</Badge>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">Input Sanitization</p>
                      <p className="text-sm text-muted-foreground">Sanitize all user inputs</p>
                    </div>
                    <Badge variant="success">Enabled</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Key className="h-5 w-5" />
                  API Keys
                </CardTitle>
                <CardDescription>
                  Manage API access keys
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-lg border p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Production API Key</p>
                      <p className="font-mono text-sm text-muted-foreground">epk_live_••••••••••••</p>
                    </div>
                    <Button variant="outline" size="sm">Regenerate</Button>
                  </div>
                </div>
                <div className="rounded-lg border p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Test API Key</p>
                      <p className="font-mono text-sm text-muted-foreground">epk_test_••••••••••••</p>
                    </div>
                    <Button variant="outline" size="sm">Regenerate</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="system" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  System Configuration
                </CardTitle>
                <CardDescription>
                  General system settings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Default Currency</Label>
                    <Select defaultValue="KES">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="KES">KES - Kenyan Shilling</SelectItem>
                        <SelectItem value="USD">USD - US Dollar</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Timezone</Label>
                    <Select defaultValue="Africa/Nairobi">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Africa/Nairobi">Africa/Nairobi (EAT)</SelectItem>
                        <SelectItem value="UTC">UTC</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Default Interest Rate (%)</Label>
                    <Input type="number" defaultValue="12" />
                  </div>
                  <div className="space-y-2">
                    <Label>Late Fee Amount (KES)</Label>
                    <Input type="number" defaultValue="500" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Grace Period (Days)</Label>
                  <Input type="number" defaultValue="7" />
                </div>
                <div className="flex justify-end">
                  <Button>Save Settings</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
