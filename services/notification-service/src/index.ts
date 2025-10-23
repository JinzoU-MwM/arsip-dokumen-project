import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import { createLogger, transports, format } from 'winston';
import { NotificationService } from './notification_service';
import { TemplateManager } from './template_manager';
import { WAHAClient } from './waha_client';
import notificationRoutes from './routes/notifications';
import healthRoutes from './routes/health';

// Load environment variables
dotenv.config();

// Configure logger
const logger = createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: format.combine(
    format.timestamp(),
    format.errors({ stack: true }),
    format.json()
  ),
  defaultMeta: { service: 'notification-service' },
  transports: [
    new transports.File({ filename: 'logs/error.log', level: 'error' }),
    new transports.File({ filename: 'logs/combined.log' }),
    new transports.Console({
      format: format.combine(
        format.colorize(),
        format.simple()
      )
    })
  ]
});

// Create Express app
const app = express();
const PORT = process.env.PORT || 8005;

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || '*',
  credentials: true
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Request logging middleware
app.use((req, res, next) => {
  logger.info('Request received', {
    method: req.method,
    path: req.path,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  });
  next();
});

// Initialize services
let notificationService: NotificationService;
let templateManager: TemplateManager;
let wahaClient: WAHAClient;

async function initializeServices() {
  try {
    logger.info('Initializing notification service...');

    // Initialize WAHA client
    wahaClient = new WAHAClient({
      baseUrl: process.env.WAHA_URL || 'http://localhost:3000',
      apiKey: process.env.WAHA_API_KEY || '',
      session: process.env.WAHA_SESSION || 'default'
    });

    // Initialize template manager
    templateManager = new TemplateManager('./templates');

    // Initialize notification service
    notificationService = new NotificationService(wahaClient, templateManager, logger);

    // Test WAHA connection
    await wahaClient.testConnection();
    logger.info('WAHA client connected successfully');

    // Load templates
    await templateManager.loadTemplates();
    logger.info('Templates loaded successfully');

    logger.info('Notification service initialized successfully');
  } catch (error) {
    logger.error('Failed to initialize services', { error: error.message });
    process.exit(1);
  }
}

// Routes
app.use('/health', healthRoutes);
app.use('/notifications', notificationRoutes(notificationService));

// Error handling middleware
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  logger.error('Unhandled error', {
    error: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method
  });

  res.status(500).json({
    success: false,
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
  });
});

// 404 handler
app.use('*', (req: express.Request, res: express.Response) => {
  res.status(404).json({
    success: false,
    error: 'Not found',
    message: `Route ${req.originalUrl} not found`
  });
});

// Graceful shutdown
process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

async function gracefulShutdown(signal: string) {
  logger.info(`Received ${signal}, starting graceful shutdown`);

  // Close HTTP server
  server.close(() => {
    logger.info('HTTP server closed');

    // Cleanup WAHA client
    if (wahaClient) {
      wahaClient.disconnect();
    }

    logger.info('Graceful shutdown completed');
    process.exit(0);
  });

  // Force close after 30 seconds
  setTimeout(() => {
    logger.error('Could not close connections in time, forcefully shutting down');
    process.exit(1);
  }, 30000);
}

// Start server
const server = app.listen(PORT, async () => {
  logger.info(`Notification service starting on port ${PORT}`);

  try {
    await initializeServices();
    logger.info(`Notification service is running on port ${PORT}`);
  } catch (error) {
    logger.error('Failed to start service', { error: error.message });
    process.exit(1);
  }
});

export default app;