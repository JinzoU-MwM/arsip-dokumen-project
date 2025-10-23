import { EventEmitter } from 'events';
import { WAHAClient } from './waha_client';
import { TemplateManager } from './template_manager';
import { Logger } from 'winston';
import { NotificationRequest, NotificationResult, NotificationChannel } from '../types/notification';

export interface NotificationServiceConfig {
  maxRetries?: number;
  retryDelay?: number;
  rateLimitPerMinute?: number;
}

export class NotificationService extends EventEmitter {
  private wahaClient: WAHAClient;
  private templateManager: TemplateManager;
  private logger: Logger;
  private config: Required<NotificationServiceConfig>;
  private rateLimitMap: Map<string, number[]> = new Map();

  constructor(
    wahaClient: WAHAClient,
    templateManager: TemplateManager,
    logger: Logger,
    config: NotificationServiceConfig = {}
  ) {
    super();
    this.wahaClient = wahaClient;
    this.templateManager = templateManager;
    this.logger = logger.child({ component: 'NotificationService' });

    this.config = {
      maxRetries: config.maxRetries || 3,
      retryDelay: config.retryDelay || 5000,
      rateLimitPerMinute: config.rateLimitPerMinute || 30
    };
  }

  async sendNotification(request: NotificationRequest): Promise<NotificationResult> {
    this.logger.info('Processing notification request', {
      type: request.notification_type,
      recipient: request.recipient,
      channels: request.channels
    });

    try {
      // Validate request
      this.validateRequest(request);

      // Check rate limiting
      await this.checkRateLimit(request.recipient);

      // Process each channel
      const results: NotificationResult[] = [];

      for (const channel of request.channels) {
        try {
          const result = await this.sendToChannel(request, channel);
          results.push(result);
        } catch (error) {
          this.logger.error('Failed to send notification to channel', {
            channel,
            error: error.message,
            recipient: request.recipient
          });

          results.push({
            success: false,
            channel,
            error: error.message,
            timestamp: new Date().toISOString()
          });
        }
      }

      // Return overall result
      const overallSuccess = results.some(r => r.success);
      const failedChannels = results.filter(r => !r.success).map(r => r.channel);

      const result: NotificationResult = {
        success: overallSuccess,
        channel: 'multi',
        timestamp: new Date().toISOString(),
        details: {
          total_channels: results.length,
          successful_channels: results.filter(r => r.success).length,
          failed_channels: failedChannels.length,
          channel_results: results
        }
      };

      if (!overallSuccess) {
        result.error = `Failed to send to channels: ${failedChannels.join(', ')}`;
      }

      this.emit('notification_sent', { request, result });
      return result;

    } catch (error) {
      this.logger.error('Notification processing failed', {
        error: error.message,
        type: request.notification_type,
        recipient: request.recipient
      });

      return {
        success: false,
        channel: 'multi',
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }

  private async sendToChannel(
    request: NotificationRequest,
    channel: NotificationChannel
  ): Promise<NotificationResult> {
    switch (channel) {
      case 'whatsapp':
        return this.sendWhatsAppNotification(request);
      case 'email':
        return this.sendEmailNotification(request);
      default:
        throw new Error(`Unsupported channel: ${channel}`);
    }
  }

  private async sendWhatsAppNotification(request: NotificationRequest): Promise<NotificationResult> {
    try {
      // Generate message using template
      const message = await this.templateManager.renderTemplate(
        request.notification_type,
        request.data
      );

      // Send via WAHA
      const result = await this.wahaClient.sendMessage({
        to: request.recipient,
        message: message,
        type: 'text'
      });

      this.logger.info('WhatsApp notification sent', {
        recipient: request.recipient,
        type: request.notification_type,
        messageId: result.messageId
      });

      return {
        success: true,
        channel: 'whatsapp',
        timestamp: new Date().toISOString(),
        details: {
          messageId: result.messageId,
          recipient: request.recipient
        }
      };

    } catch (error) {
      this.logger.error('WhatsApp notification failed', {
        error: error.message,
        recipient: request.recipient
      });
      throw error;
    }
  }

  private async sendEmailNotification(request: NotificationRequest): Promise<NotificationResult> {
    // TODO: Implement email notification
    this.logger.info('Email notification not yet implemented', {
      recipient: request.recipient,
      type: request.notification_type
    });

    return {
      success: false,
      channel: 'email',
      error: 'Email notifications not yet implemented',
      timestamp: new Date().toISOString()
    };
  }

  private validateRequest(request: NotificationRequest): void {
    if (!request.recipient) {
      throw new Error('Recipient is required');
    }

    if (!request.notification_type) {
      throw new Error('Notification type is required');
    }

    if (!request.channels || request.channels.length === 0) {
      throw new Error('At least one channel must be specified');
    }

    if (!request.data) {
      throw new Error('Notification data is required');
    }
  }

  private async checkRateLimit(recipient: string): Promise<void> {
    const now = Date.now();
    const oneMinuteAgo = now - 60000;

    // Get existing requests for this recipient
    const requests = this.rateLimitMap.get(recipient) || [];

    // Filter out old requests (older than 1 minute)
    const recentRequests = requests.filter(timestamp => timestamp > oneMinuteAgo);

    // Check if rate limit exceeded
    if (recentRequests.length >= this.config.rateLimitPerMinute) {
      throw new Error(`Rate limit exceeded for ${recipient}. Max ${this.config.rateLimitPerMinute} notifications per minute.`);
    }

    // Add current request
    recentRequests.push(now);
    this.rateLimitMap.set(recipient, recentRequests);
  }

  async sendBulkNotifications(requests: NotificationRequest[]): Promise<NotificationResult[]> {
    this.logger.info('Processing bulk notifications', {
      count: requests.length
    });

    const results: NotificationResult[] = [];

    // Process notifications concurrently but with rate limiting
    const concurrencyLimit = 10;
    const chunks = [];

    for (let i = 0; i < requests.length; i += concurrencyLimit) {
      chunks.push(requests.slice(i, i + concurrencyLimit));
    }

    for (const chunk of chunks) {
      const chunkPromises = chunk.map(request => this.sendNotification(request));
      const chunkResults = await Promise.allSettled(chunkPromises);

      chunkResults.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          results.push(result.value);
        } else {
          results.push({
            success: false,
            channel: 'multi',
            error: result.reason.message,
            timestamp: new Date().toISOString()
          });
        }
      });

      // Small delay between chunks to prevent rate limiting
      if (chunks.indexOf(chunk) < chunks.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }

    const successCount = results.filter(r => r.success).length;
    this.logger.info('Bulk notifications completed', {
      total: requests.length,
      successful: successCount,
      failed: requests.length - successCount
    });

    return results;
  }

  getNotificationStatus(notificationId: string): Promise<any> {
    // TODO: Implement notification status tracking
    throw new Error('Notification status tracking not yet implemented');
  }

  async cancelNotification(notificationId: string): Promise<boolean> {
    // TODO: Implement notification cancellation
    this.logger.info('Notification cancellation not yet implemented', {
      notificationId
    });
    return false;
  }
}