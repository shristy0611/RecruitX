import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { S3Client, PutObjectCommand, ListBucketsCommand, CreateBucketCommand } from '@aws-sdk/client-s3';
import { createPresignedPost } from '@aws-sdk/s3-presigned-post';
import { authOptions } from '@/auth/options';
import { prisma } from '@/lib/prisma';
import { FileType } from '@prisma/client';

// S3/MinIO client
const s3Client = new S3Client({
  region: 'us-east-1',
  endpoint: process.env.NODE_ENV === 'production' 
    ? undefined 
    : 'http://localhost:9000',
  forcePathStyle: true, // Required for MinIO
  credentials: {
    accessKeyId: process.env.NODE_ENV === 'production'
      ? process.env.AWS_ACCESS_KEY_ID || ''
      : 'minio',
    secretAccessKey: process.env.NODE_ENV === 'production'
      ? process.env.AWS_SECRET_ACCESS_KEY || ''
      : 'minio123',
  },
});

// Bucket to use for storage
const BUCKET_NAME = process.env.S3_BUCKET_NAME || 'recruitx-files';

export async function POST(request: NextRequest) {
  try {
    // Get user session
    const session = await getServerSession(authOptions);
    
    if (!session?.user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }
    
    // Get user ID (with type safety)
    const userId = session.user.id || session.user.email;
    
    if (!userId) {
      return NextResponse.json(
        { error: 'User identification missing' },
        { status: 400 }
      );
    }

    // Get request body
    const body = await request.json();
    const { fileName, fileType, contentType } = body;
    
    if (!fileName || !fileType || !contentType) {
      return NextResponse.json(
        { error: 'Missing required parameters' },
        { status: 400 }
      );
    }
    
    // Validate fileType
    if (!Object.values(FileType).includes(fileType as FileType)) {
      return NextResponse.json(
        { error: 'Invalid file type' },
        { status: 400 }
      );
    }
    
    // Create a unique key for the file
    const key = `${session.user.id}/${Date.now()}-${fileName}`;
    
    // Create presigned URL for direct upload to S3/MinIO
    const { url, fields } = await createPresignedPost(s3Client, {
      Bucket: BUCKET_NAME,
      Key: key,
      Conditions: [
        ['content-length-range', 0, 10485760], // 10MB max
        ['eq', '$Content-Type', contentType],
      ],
      Expires: 600, // 10 minutes
    });
    
    // Create file record in database
    const file = await prisma.file.create({
      data: {
        originalName: fileName,
        s3Key: key,
        type: fileType as FileType,
        status: 'UPLOADED',
        userId: userId.toString(), // Ensure it's a string
      },
    });
    
    return NextResponse.json({
      fileId: file.id,
      uploadUrl: url,
      fields,
    });
    
  } catch (error) {
    console.error('Error creating presigned URL:', error);
    return NextResponse.json(
      { error: 'Failed to generate upload URL' },
      { status: 500 }
    );
  }
}

// Initialize S3 bucket if it doesn't exist
async function ensureBucketExists() {
  try {
    // Check if bucket exists
    const listCommand = new ListBucketsCommand();
    const { Buckets } = await s3Client.send(listCommand);
    
    const bucketExists = Buckets?.some(bucket => bucket.Name === BUCKET_NAME);
    
    if (!bucketExists) {
      const createCommand = new CreateBucketCommand({
        Bucket: BUCKET_NAME,
      });
      await s3Client.send(createCommand);
      console.log(`Created bucket: ${BUCKET_NAME}`);
    }
  } catch (error) {
    console.error('Error ensuring bucket exists:', error);
  }
}

// Initialize bucket when server starts
// This runs only once in production, but on every reload in development
ensureBucketExists().catch(console.error);
