import { Router, Request, Response } from 'express';
import { NotificationService } from '../notification_service';
import { NotificationRequest } from '../types/notification';
import Joi from 'joi';

const router = Router();

// Validation schemas
const notificationSchema = Joi.object({
  recipient: Joi.string().required(),
  notification_type: Joi.string().required(),
  channels: Joi.array().items(Joi.string().valid('whatsapp', 'email', 'sms', 'push')).min(1).required(),
  data: Joi.object().required(),
  priority: Joi.string().valid('low', 'normal', 'high', 'urgent').default('normal'),
  scheduled_at: Joi.date().iso().optional(),
  metadata: Joi.object().optional()
});

const bulkNotificationSchema = Joi.object({
  notifications: Joi.array().items(notificationSchema).min(1).max(100).required()
});

export default function createNotificationRoutes(notificationService: NotificationService): Router {
  // Send single notification
  router.post('/send-notification', async (req: Request, res: Response) => {
    try {
      // Validate request
      const { error, value } = notificationSchema.validate(req.body);
      if (error) {
        return res.status(400).json({
          success: false,
          error: 'Validation error',
          details: error.details.map(d => d.message)
        });
      }

      const notificationRequest: NotificationRequest = value;

      // Send notification
      const result = await notificationService.sendNotification(notificationRequest);

      return res.status(200).json({
        success: true,
        message: 'Notification processed',
        result
      });

    } catch (error) {
      console.error('Send notification error:', error);
      return res.status(500).json({
        success: false,
        error: 'Internal server error',
        message: error.message
      });
    }
  });

  // Send bulk notifications
  router.post('/send-bulk', async (req: Request, res: Response) => {
    try {
      // Validate request
      const { error, value } = bulkNotificationSchema.validate(req.body);
      if (error) {
        return res.status(400).json({
          success: false,
          error: 'Validation error',
          details: error.details.map(d => d.message)
        });
      }

      const { notifications } = value;

      // Send bulk notifications
      const results = await notificationService.sendBulkNotifications(notifications);

      const successCount = results.filter(r => r.success).length;

      return res.status(200).json({
        success: true,
        message: 'Bulk notifications processed',
        results: {
          total: notifications.length,
          successful: successCount,
          failed: notifications.length - successCount,
          details: results
        }
      });

    } catch (error) {
      console.error('Send bulk notifications error:', error);
      return res.status(500).json({
        success: false,
        error: 'Internal server error',
        message: error.message
      });
    }
  });

  // Get notification status
  router.get('/status/:notificationId', async (req: Request, res: Response) => {
    try {
      const { notificationId } = req.params;

      const status = await notificationService.getNotificationStatus(notificationId);

      return res.status(200).json({
        success: true,
        data: status
      });

    } catch (error) {
      console.error('Get notification status error:', error);
      return res.status(500).json({
        success: false,
        error: 'Internal server error',
        message: error.message
      });
    }
  });

  // Cancel notification
  router.delete('/:notificationId', async (req: Request, res: Response) => {
    try {
      const { notificationId } = req.params;

      const cancelled = await notificationService.cancelNotification(notificationId);

      return res.status(200).json({
        success: cancelled,
        message: cancelled ? 'Notification cancelled' : 'Failed to cancel notification'
      });

    } catch (error) {
      console.error('Cancel notification error:', error);
      return res.status(500).json({
        success: false,
        error: 'Internal server error',
        message: error.message
      });
    }
  });

  // Health check
  router.get('/health', (req: Request, res: Response) => {
    res.status(200).json({
      success: true,
      service: 'notification-service',
      status: 'healthy',
      timestamp: new Date().toISOString()
    });
  });

  return router;
}