export type NotificationChannel = 'whatsapp' | 'email' | 'sms' | 'push';

export interface NotificationRequest {
  recipient: string; // Phone number for WhatsApp, email for email, etc.
  notification_type: string;
  channels: NotificationChannel[];
  data: Record<string, any>;
  priority?: 'low' | 'normal' | 'high' | 'urgent';
  scheduled_at?: string; // ISO timestamp for scheduled sending
  metadata?: Record<string, any>;
}

export interface NotificationResult {
  success: boolean;
  channel: NotificationChannel | 'multi';
  timestamp: string;
  error?: string;
  details?: Record<string, any>;
}

export interface TemplateData {
  [key: string]: any;
}

export interface WhatsAppMessage {
  to: string;
  message: string;
  type: 'text' | 'image' | 'document' | 'interactive';
  mediaUrl?: string;
  caption?: string;
  buttons?: WhatsAppButton[];
  header?: WhatsAppHeader;
  footer?: string;
}

export interface WhatsAppButton {
  id: string;
  text: string;
  type: 'reply' | 'url';
  url?: string;
}

export interface WhatsAppHeader {
  type: 'text' | 'image' | 'document';
  text?: string;
  mediaUrl?: string;
}

export interface WAHAResponse {
  success: boolean;
  messageId?: string;
  error?: string;
  data?: any;
}