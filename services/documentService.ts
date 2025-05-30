import { CVData, JobDescriptionData } from '../types';

/**
 * Service for managing document (CV and JD) operations
 * Currently uses localStorage, but will be expanded to use vector database
 */
class DocumentService {
  /**
   * Retrieve a document by its ID
   * @param id The document ID to retrieve
   * @returns The document if found, otherwise null
   */
  async getDocumentById(id: string): Promise<CVData | JobDescriptionData | null> {
    try {
      // Check if it's a CV
      const storedCvsString = localStorage.getItem('recruitx_cvs');
      if (storedCvsString) {
        const cvs = JSON.parse(storedCvsString) as CVData[];
        const cv = cvs.find(cv => cv.id === id);
        if (cv) return cv;
      }
      
      // Check if it's a JD
      const storedJdsString = localStorage.getItem('recruitx_jds');
      if (storedJdsString) {
        const jds = JSON.parse(storedJdsString) as JobDescriptionData[];
        const jd = jds.find(jd => jd.id === id);
        if (jd) return jd;
      }
      
      // Not found
      return null;
    } catch (error) {
      console.error("Error retrieving document:", error);
      throw new Error(`Document retrieval error: ${(error as Error).message}`);
    }
  }
  
  /**
   * Save or update a document
   * @param document The document to save or update
   * @returns The saved/updated document
   */
  async saveDocument(document: CVData | JobDescriptionData): Promise<CVData | JobDescriptionData> {
    try {
      if ('cvMimeType' in document) {
        // It's a CV
        const storedCvsString = localStorage.getItem('recruitx_cvs');
        const cvs = storedCvsString ? JSON.parse(storedCvsString) as CVData[] : [];
        
        // Find and update existing or add new
        const existingIndex = cvs.findIndex(cv => cv.id === document.id);
        if (existingIndex >= 0) {
          cvs[existingIndex] = document as CVData;
        } else {
          cvs.push(document as CVData);
        }
        
        localStorage.setItem('recruitx_cvs', JSON.stringify(cvs));
      } else {
        // It's a JD
        const storedJdsString = localStorage.getItem('recruitx_jds');
        const jds = storedJdsString ? JSON.parse(storedJdsString) as JobDescriptionData[] : [];
        
        // Find and update existing or add new
        const existingIndex = jds.findIndex(jd => jd.id === document.id);
        if (existingIndex >= 0) {
          jds[existingIndex] = document as JobDescriptionData;
        } else {
          jds.push(document as JobDescriptionData);
        }
        
        localStorage.setItem('recruitx_jds', JSON.stringify(jds));
      }
      
      return document;
    } catch (error) {
      console.error("Error saving document:", error);
      throw new Error(`Document save error: ${(error as Error).message}`);
    }
  }
  
  /**
   * Delete a document by its ID
   * @param id The document ID to delete
   * @returns True if deleted, false if not found
   */
  async deleteDocument(id: string): Promise<boolean> {
    try {
      let deleted = false;
      
      // Check if it's a CV
      const storedCvsString = localStorage.getItem('recruitx_cvs');
      if (storedCvsString) {
        const cvs = JSON.parse(storedCvsString) as CVData[];
        const initialLength = cvs.length;
        const filteredCvs = cvs.filter(cv => cv.id !== id);
        
        if (filteredCvs.length < initialLength) {
          localStorage.setItem('recruitx_cvs', JSON.stringify(filteredCvs));
          deleted = true;
        }
      }
      
      // If not found in CVs, check JDs
      if (!deleted) {
        const storedJdsString = localStorage.getItem('recruitx_jds');
        if (storedJdsString) {
          const jds = JSON.parse(storedJdsString) as JobDescriptionData[];
          const initialLength = jds.length;
          const filteredJds = jds.filter(jd => jd.id !== id);
          
          if (filteredJds.length < initialLength) {
            localStorage.setItem('recruitx_jds', JSON.stringify(filteredJds));
            deleted = true;
          }
        }
      }
      
      return deleted;
    } catch (error) {
      console.error("Error deleting document:", error);
      throw new Error(`Document deletion error: ${(error as Error).message}`);
    }
  }
}

export const documentService = new DocumentService(); 