import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';
import { authOptions } from '@/auth/options';
import { prisma } from '@/lib/prisma';

// S3/MinIO client - matches the one used in upload route
const s3Client = new S3Client({
  region: 'us-east-1',
  endpoint: process.env.NODE_ENV === 'production' 
    ? undefined 
    : 'http://localhost:9000',
  forcePathStyle: true,
  credentials: {
    accessKeyId: process.env.NODE_ENV === 'production'
      ? process.env.AWS_ACCESS_KEY_ID || ''
      : 'minio',
    secretAccessKey: process.env.NODE_ENV === 'production'
      ? process.env.AWS_SECRET_ACCESS_KEY || ''
      : 'minio123',
  },
});

// Bucket name
const BUCKET_NAME = process.env.S3_BUCKET_NAME || 'recruitx-files';

/**
 * Endpoint to trigger file text extraction process
 */
export async function POST(request: NextRequest) {
  try {
    // Get user session
    const session = await getServerSession(authOptions);
    
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Get user ID (with type safety)
    const userId = session.user.id || session.user.email; // Fallback to email if ID doesn't exist
    
    if (!userId) {
      return NextResponse.json({ error: 'User identification missing' }, { status: 400 });
    }

    // Get request body
    const body = await request.json();
    const { fileId } = body;
    
    if (!fileId) {
      return NextResponse.json({ error: 'Missing fileId' }, { status: 400 });
    }
    
    // Get file from database
    const file = await prisma.file.findUnique({
      where: { id: fileId },
    });
    
    if (!file) {
      return NextResponse.json({ error: 'File not found' }, { status: 404 });
    }
    
    // Check file ownership or admin permissions
    if (file.userId !== userId) {
      return NextResponse.json({ error: 'Access denied' }, { status: 403 });
    }
    
    // Extract text from file
    const extractedText = await extractTextFromFile(file.s3Key);
    
    // Create extraction record in database
    const extraction = await prisma.extraction.create({
      data: {
        fileId: file.id,
        rawText: extractedText,
        status: 'EXTRACTED',
        versions: [{ version: 1, text: extractedText, timestamp: new Date() }],
      },
    });
    
    // Update file status
    await prisma.file.update({
      where: { id: file.id },
      data: { status: 'EXTRACTED' },
    });
    
    return NextResponse.json({
      success: true,
      extractionId: extraction.id,
    });
    
  } catch (error) {
    console.error('Error extracting text:', error);
    return NextResponse.json(
      { error: 'Text extraction failed' },
      { status: 500 }
    );
  }
}

/**
 * Extract text from a file in S3/MinIO
 */
async function extractTextFromFile(s3Key: string): Promise<string> {
  try {
    // Get file from S3/MinIO
    const command = new GetObjectCommand({
      Bucket: BUCKET_NAME,
      Key: s3Key,
    });
    
    const response = await s3Client.send(command);
    
    if (!response.Body) {
      throw new Error('Empty file body');
    }
    
    // Convert stream to text
    const chunks: Uint8Array[] = [];
    const stream = response.Body as ReadableStream<Uint8Array>;
    const reader = stream.getReader();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (value) chunks.push(value);
    }
    
    const buffer = Buffer.concat(chunks);
    
    // The actual text extraction depends on file type
    // This is a simplified version - in reality would use proper extractors for each file type
    // This would connect to libraries like pdf.js, docx-parser, xlsx-parser, etc.
    
    // For now, assume it's a text/plain file
    const extractedText = buffer.toString('utf-8');
    
    // In a production app, we would:
    // 1. Detect file type from MIME or extension
    // 2. Call appropriate extractor
    // 3. Clean and structure the extracted text
    // 4. Return the text
    
    return extractedText;
  } catch (error) {
    console.error('Error extracting text from file:', error);
    throw new Error('Failed to extract text from file');
  }
}
