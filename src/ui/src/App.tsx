import React from 'react'; // Added to resolve UMD global reference issues
import { useState } from 'react'
import { Menu, X, ChevronRight, MessageSquare, Users, FileText, BarChart, BrainCircuit, Briefcase } from 'lucide-react'
import { ModelContextProvider } from './contexts/ModelContext'
import ChatInterface from './components/ChatInterface'
import ModelSelector from './components/ModelSelector'
import ResumeAnalyzer from './components/ResumeAnalyzer'
import JobUploader from '@/components/JobUploader'
import SourcingAgentUI from '@/components/SourcingAgentUI'
import MatchingAgentUI from '@/components/MatchingAgentUI'
import EngagementAgentUI from '@/components/EngagementAgentUI'

function App() {  
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [activeTab, setActiveTab] = useState<'dashboard' | 'chat' | 'resume' | 'job' | 'sourcing' | 'matching' | 'engagement'>('dashboard')

  const menuItems = [
    { icon: BrainCircuit, label: 'Dashboard', id: 'dashboard' as const },
    { icon: MessageSquare, label: 'AI Chat', id: 'chat' as const },
    { icon: FileText, label: 'Resume Analyzer', id: 'resume' as const },
    { icon: Briefcase, label: 'Job Uploader', id: 'job' as const },
    { icon: Users, label: 'Sourcing', id: 'sourcing' as const },
    { icon: BarChart, label: 'Matching', id: 'matching' as const },
    { icon: BrainCircuit, label: 'Engagement', id: 'engagement' as const },
  ]

  return (
    <ModelContextProvider>
      <div className="min-h-screen bg-background text-foreground">
        {/* Sidebar */}
        <aside
          className={`fixed top-0 left-0 z-40 h-screen transition-transform ${
            isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
          } glass-card w-64 border-r border-white/10`}
        >
          <div className="flex h-16 items-center justify-between px-6">
            <h1 className="text-xl font-semibold gradient-text">RecruitX</h1>
            <button
              onClick={() => setIsSidebarOpen(false)}
              className="rounded-lg p-1.5 hover:bg-white/5"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="px-4 py-2">
            <div className="py-1 px-2 text-xs font-medium text-muted-foreground uppercase">
              Main Menu
            </div>
          </div>

          <nav className="px-3">
            {menuItems.map((item) => (
              <a
                key={item.label}
                href="#"
                onClick={(e) => {
                  e.preventDefault()
                  if ('id' in item) {
                    setActiveTab(item.id)
                  }
                }}
                className={`flex items-center justify-between rounded-lg px-3 py-2 text-sm mb-1 transition-colors ${
                  'id' in item && activeTab === item.id
                    ? 'bg-primary/20 text-primary'
                    : 'hover:bg-white/5'
                }`}
              >
                <div className="flex items-center gap-3">
                  <item.icon className="h-5 w-5" />
                  <span>{item.label}</span>
                </div>
              </a>
            ))}
          </nav>

          <div className="absolute bottom-0 left-0 right-0 p-4">
            <ModelSelector />
          </div>
        </aside>

        {/* Main content */}
        <main
          className={`min-h-screen transition-all duration-300 ${
            isSidebarOpen ? 'pl-64' : 'pl-0'
          }`}
        >
          <header className="sticky top-0 z-30 glass-card border-b border-white/10">
            <div className="flex h-16 items-center gap-3 px-6">
              {!isSidebarOpen && (
                <button
                  onClick={() => setIsSidebarOpen(true)}
                  className="rounded-lg p-1.5 hover:bg-white/5"
                >
                  <Menu className="h-5 w-5" />
                </button>
              )}
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-medium">
                  {activeTab === 'dashboard' 
                    ? 'Dashboard' 
                    : activeTab === 'chat' 
                    ? 'AI Chat' 
                    : activeTab === 'resume'
                    ? 'Resume Analyzer'
                    : activeTab === 'job'
                    ? 'Job Uploader'
                    : activeTab === 'sourcing'
                    ? 'Sourcing'
                    : activeTab === 'matching'
                    ? 'Matching'
                    : 'Engagement'}
                </h2>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">RecruitX AI Platform</span>
              </div>
            </div>
          </header>

          <div className="container py-8">
            {activeTab === 'dashboard' && (
              <>
                <div className="mb-8">
                  <h1 className="text-3xl font-bold mb-2">Welcome to RecruitX</h1>
                  <p className="text-muted-foreground">
                    AI-powered recruitment platform with dual-model capabilities
                  </p>
                </div>

                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                  {menuItems.map((item) => (
                    <div key={item.label} className="glass-card p-6">
                      <div className="flex items-center gap-4">
                        <div className="rounded-full bg-primary/10 p-3">
                          <item.icon className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">{item.label}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                  <div className="glass-card p-6 rounded-xl">
                    <h3 className="text-lg font-medium mb-4">Key Features</h3>
                    <div className="space-y-3">
                      <div className="flex items-start gap-3">
                        <div className="rounded-full bg-green-500/10 p-1.5 mt-0.5">
                          <Check className="h-4 w-4 text-green-500" />
                        </div>
                        <div>
                          <p className="font-medium">Dual AI Model Support</p>
                          <p className="text-sm text-muted-foreground">
                            Choose between Gemma 3 (local) or Gemini (cloud) for all operations
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start gap-3">
                        <div className="rounded-full bg-green-500/10 p-1.5 mt-0.5">
                          <Check className="h-4 w-4 text-green-500" />
                        </div>
                        <div>
                          <p className="font-medium">Resume Analysis</p>
                          <p className="text-sm text-muted-foreground">
                            Automated skill extraction, candidate evaluation, and fit scoring
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start gap-3">
                        <div className="rounded-full bg-green-500/10 p-1.5 mt-0.5">
                          <Check className="h-4 w-4 text-green-500" />
                        </div>
                        <div>
                          <p className="font-medium">Job Uploader</p>
                          <p className="text-sm text-muted-foreground">
                            Upload job descriptions for AI-powered matching and analysis
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="glass-card p-6 rounded-xl">
                    <h3 className="text-lg font-medium mb-4">Recent Activity</h3>
                    <div className="space-y-4">
                      {[
                        { action: 'Resume analyzed', time: '2 hours ago' },
                        { action: 'New candidate application', time: '4 hours ago' },
                        { action: 'Job description generated', time: '1 day ago' }
                      ].map((activity, i) => (
                        <div key={i} className="flex items-center gap-4">
                          <div className="h-9 w-9 rounded-full bg-primary/10" />
                          <div>
                            <p className="text-sm">{activity.action}</p>
                            <p className="text-xs text-muted-foreground">{activity.time}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </>
            )}

            {activeTab === 'chat' && (
              <div className="h-[calc(100vh-12rem)]">
                <ChatInterface />
              </div>
            )}

            {activeTab === 'resume' && <ResumeAnalyzer />}

            {activeTab === 'job' && <JobUploader />}

            {activeTab === 'sourcing' && <SourcingAgentUI />}

            {activeTab === 'matching' && <MatchingAgentUI />}

            {activeTab === 'engagement' && <EngagementAgentUI />}
          </div>
        </main>
      </div>
    </ModelContextProvider>
  )
}

export default App

// This component is missing in the original code, so we define it here
function Check(props: any) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M20 6 9 17l-5-5" />
    </svg>
  )
}