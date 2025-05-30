// Vector Database Integration Service
// This service handles document embedding and retrieval operations

import { OpenAI } from 'openai';

// Initialize OpenAI client - will be properly configured during deployment
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || 'dummy-key-for-development',
});

// Document types that can be embedded
export type DocumentType = 'cv' | 'jd';

// Mock vector database for local development
// Will be replaced with actual Pinecone/Qdrant integration
class LocalVectorStore {
  private embeddings: Array<{
    id: string;
    values: number[];
    metadata: Record<string, any>;
  }> = [];

  async upsert(record: { id: string; values: number[]; metadata: Record<string, any> }) {
    // Remove if exists
    this.embeddings = this.embeddings.filter(item => item.id !== record.id);
    // Add new record
    this.embeddings.push(record);
    return { upserted: 1 };
  }

  async query(queryVector: number[], topK: number = 5) {
    // Simple cosine similarity implementation
    const results = this.embeddings.map(item => {
      const similarity = cosineSimilarity(queryVector, item.values);
      return {
        id: item.id,
        score: similarity,
        metadata: item.metadata,
      };
    });

    // Sort by similarity score (descending)
    results.sort((a, b) => b.score - a.score);
    
    // Return top K results
    return {
      matches: results.slice(0, topK)
    };
  }
}

// Initialize local vector store (will be replaced with actual DB in production)
const vectorDB = new LocalVectorStore();

/**
 * Generates an embedding for a document and stores it in the vector database
 * @param content The text content to embed
 * @param type The type of document (cv or jd)
 * @param id Unique identifier for the document
 * @returns The result of the upsert operation
 */
export async function embedDocument(content: string, type: DocumentType, id: string) {
  try {
    const embedding = await openai.embeddings.create({ 
      input: content, 
      model: "text-embedding-3-large" 
    });
    
    return vectorDB.upsert({ 
      id, 
      values: embedding.data[0].embedding, 
      metadata: { type, timestamp: new Date().toISOString() } 
    });
  } catch (error) {
    console.error("Error embedding document:", error);
    throw new Error(`Failed to embed document: ${(error as Error).message}`);
  }
}

/**
 * Finds semantically similar documents based on a query
 * @param queryText The text to search for
 * @param type Optional filter by document type
 * @param topK Number of results to return
 * @returns Array of matching documents with similarity scores
 */
export async function findSimilarDocuments(queryText: string, type?: DocumentType, topK: number = 5) {
  try {
    // Generate embedding for the query text
    const embedding = await openai.embeddings.create({
      input: queryText,
      model: "text-embedding-3-large"
    });
    
    // Query the vector database
    const results = await vectorDB.query(embedding.data[0].embedding, topK);
    
    // Filter by type if specified
    if (type) {
      results.matches = results.matches.filter(match => match.metadata.type === type);
    }
    
    return results.matches;
  } catch (error) {
    console.error("Error finding similar documents:", error);
    throw new Error(`Failed to find similar documents: ${(error as Error).message}`);
  }
}

// Utility function to calculate cosine similarity between two vectors
function cosineSimilarity(vecA: number[], vecB: number[]): number {
  if (vecA.length !== vecB.length) {
    throw new Error("Vectors must have the same dimensions");
  }

  let dotProduct = 0;
  let normA = 0;
  let normB = 0;

  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    normA += vecA[i] * vecA[i];
    normB += vecB[i] * vecB[i];
  }

  if (normA === 0 || normB === 0) {
    return 0;
  }

  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

export default {
  embedDocument,
  findSimilarDocuments,
}; 