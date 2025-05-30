/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_KEY: string;
  // more env variables...
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Add declaration for pdfjs-dist module
declare module 'pdfjs-dist/build/pdf.mjs' {
  export const getDocument: any;
  export const GlobalWorkerOptions: {
    workerSrc: string;
  };
  export type PDFDocumentProxy = any;
} 