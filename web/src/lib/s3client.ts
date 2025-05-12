import { S3Client } from '@aws-sdk/client-s3';

// MinIO client configured for local development
// In production, this would use standard AWS credentials
const s3Client = new S3Client({
  region: 'us-east-1', // MinIO default region
  endpoint: 'http://localhost:9000', // MinIO endpoint
  forcePathStyle: true, // Required for MinIO
  credentials: {
    accessKeyId: 'minio',     // From docker-compose environment
    secretAccessKey: 'minio123', // From docker-compose environment
  },
});

export default s3Client;
