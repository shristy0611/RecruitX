import Image from "next/image";
import Link from "next/link";
import { headers } from "next/headers";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex flex-col">
      {/* Hero Section */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="font-bold text-2xl text-blue-600">RecruitX</div>
          <div className="flex space-x-4">
            <Link href="/dashboard" className="px-4 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100">
              Dashboard
            </Link>
            <Link href="/api/auth/signin" className="px-4 py-2 rounded-md text-sm font-medium bg-blue-600 text-white hover:bg-blue-700">
              Sign In
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-grow">
        <section className="py-20 sm:py-32 flex flex-col items-center text-center">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <h1 className="text-4xl sm:text-6xl font-bold text-gray-900 tracking-tight">
              CV & Job Description <span className="text-blue-600">Matching</span> with AI
            </h1>
            <p className="mt-6 text-xl text-gray-600 max-w-3xl mx-auto">
              RecruitX uses cutting-edge AI to precisely match candidates with job descriptions, saving recruiters time and improving hiring outcomes.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/dashboard" className="px-6 py-3 rounded-md text-base font-medium bg-blue-600 text-white hover:bg-blue-700 shadow-sm">
                Get Started
              </Link>
              <Link href="/docs" className="px-6 py-3 rounded-md text-base font-medium bg-white text-blue-600 border border-blue-200 hover:bg-blue-50 shadow-sm">
                Learn More
              </Link>
            </div>
          </div>
        </section>

        <section className="py-16 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-gray-900">How It Works</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="p-6 bg-blue-50 rounded-lg">
                <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mb-4 font-bold text-xl">1</div>
                <h3 className="text-xl font-semibold mb-2">Upload Documents</h3>
                <p className="text-gray-600">Upload CVs and job descriptions in various formats including PDF, DOC, DOCX, and more.</p>
              </div>
              <div className="p-6 bg-blue-50 rounded-lg">
                <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mb-4 font-bold text-xl">2</div>
                <h3 className="text-xl font-semibold mb-2">AI Analysis</h3>
                <p className="text-gray-600">Our AI extracts and analyzes the content, identifying key skills, experience, and cultural fit factors.</p>
              </div>
              <div className="p-6 bg-blue-50 rounded-lg">
                <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mb-4 font-bold text-xl">3</div>
                <h3 className="text-xl font-semibold mb-2">Detailed Reports</h3>
                <p className="text-gray-600">Receive comprehensive matching reports that highlight strengths and potential gaps.</p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between">
            <div className="mb-8 md:mb-0">
              <div className="font-bold text-2xl mb-4">RecruitX</div>
              <p className="text-gray-400">AI-powered recruitment tools</p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-8">
              <div>
                <h3 className="text-sm font-semibold text-gray-300 tracking-wider uppercase mb-4">Product</h3>
                <ul className="space-y-2">
                  <li><Link href="/dashboard" className="text-gray-400 hover:text-white">Dashboard</Link></li>
                  <li><Link href="/pricing" className="text-gray-400 hover:text-white">Pricing</Link></li>
                </ul>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-300 tracking-wider uppercase mb-4">Support</h3>
                <ul className="space-y-2">
                  <li><Link href="/docs" className="text-gray-400 hover:text-white">Documentation</Link></li>
                  <li><Link href="/contact" className="text-gray-400 hover:text-white">Contact</Link></li>
                </ul>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-300 tracking-wider uppercase mb-4">Legal</h3>
                <ul className="space-y-2">
                  <li><Link href="/privacy" className="text-gray-400 hover:text-white">Privacy</Link></li>
                  <li><Link href="/terms" className="text-gray-400 hover:text-white">Terms of Service</Link></li>
                </ul>
              </div>
            </div>
          </div>
          <div className="mt-12 border-t border-gray-800 pt-8">
            <p className="text-gray-400 text-sm text-center">© 2025 RecruitX. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
