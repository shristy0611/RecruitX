import { Suspense } from 'react';
import UploadDocuments from '@/components/UploadDocuments';

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">RecruitX Dashboard</h1>
        </div>
      </header>
      <main>
        <div className="mx-auto max-w-7xl py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="rounded-lg border-4 border-dashed border-gray-200 p-4 bg-white">
              <Suspense fallback={<div>Loading...</div>}>
                <UploadDocuments />
              </Suspense>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
