import React, { useState } from 'react';
import { Briefcase, Sparkles, Loader2, Building, MapPin, DollarSign, List, Clipboard } from 'lucide-react';
import { apiService } from '../services/api';
import { useModel } from '../contexts/ModelContext';

interface JobRequirement {
  title: string;
  company: string;
  location: string;
  salary: string;
  description: string;
  requirements: string[];
  benefits: string[];
  keyResponsibilities: string[];
}

const JobDescriptionGenerator: React.FC = () => {
  const { activeModel, isModelLoading, setIsModelLoading } = useModel();
  const [jobTitle, setJobTitle] = useState('');
  const [jobDescription, setJobDescription] = useState<JobRequirement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const generateJobDescription = async () => {
    if (!jobTitle.trim() || isModelLoading) return;

    setIsModelLoading(true);
    setError(null);

    try {
      const result = await apiService.generateJobDescription({ title: jobTitle }, activeModel);
      setJobDescription(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate job description');
      console.error(err);
    } finally {
      setIsModelLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!jobDescription) return;

    const formattedJobDesc = `
# ${jobDescription.title}
${jobDescription.company} | ${jobDescription.location} | ${jobDescription.salary}

## Job Description
${jobDescription.description}

## Requirements
${jobDescription.requirements.map(req => `- ${req}`).join('\n')}

## Key Responsibilities
${jobDescription.keyResponsibilities.map(resp => `- ${resp}`).join('\n')}

## Benefits
${jobDescription.benefits.map(benefit => `- ${benefit}`).join('\n')}
    `;

    navigator.clipboard.writeText(formattedJobDesc).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleSampleJob = () => {
    setJobTitle('Senior Frontend Developer');
  };

  return (
    <div className="glass-card p-6 rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 rounded-full bg-primary/20">
          <Briefcase className="w-5 h-5 text-primary" />
        </div>
        <h3 className="text-lg font-medium">Job Description Generator</h3>
      </div>

      {!jobDescription ? (
        <div className="space-y-4">
          <div className="p-4 border border-dashed border-white/20 rounded-lg">
            <input
              type="text"
              className="w-full p-3 bg-transparent text-foreground focus:outline-none font-medium text-xl"
              placeholder="Enter job title (e.g. Senior Frontend Developer)"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              disabled={isModelLoading}
            />
          </div>

          {error && (
            <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-lg">
              <p>{error}</p>
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={handleSampleJob}
              disabled={isModelLoading}
              className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-white/10 hover:bg-white/5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Briefcase className="w-4 h-4" />
              Use Sample Job Title
            </button>

            <button
              onClick={generateJobDescription}
              disabled={!jobTitle.trim() || isModelLoading}
              className="flex-1 flex items-center justify-center gap-2 p-2 rounded-lg bg-primary text-primary-foreground font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isModelLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Generate with {activeModel === 'gemma' ? 'Gemma 3' : 'Gemini'}
                </>
              )}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="space-y-3">
            <h2 className="text-2xl font-bold">{jobDescription.title}</h2>
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <Building className="w-4 h-4" />
                <span>{jobDescription.company}</span>
              </div>
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <MapPin className="w-4 h-4" />
                <span>{jobDescription.location}</span>
              </div>
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <DollarSign className="w-4 h-4" />
                <span>{jobDescription.salary}</span>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-medium mb-2">Job Description</h3>
            <p className="text-sm text-muted-foreground">{jobDescription.description}</p>
          </div>

          <div>
            <h3 className="text-lg font-medium mb-2">Requirements</h3>
            <ul className="space-y-1.5">
              {jobDescription.requirements.map((req, index) => (
                <li key={index} className="flex items-start gap-2">
                  <div className="mt-1 rounded-full bg-green-500/20 p-0.5">
                    <List className="w-3 h-3 text-green-500" />
                  </div>
                  <span className="text-sm">{req}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-medium mb-2">Key Responsibilities</h3>
            <ul className="space-y-1.5">
              {jobDescription.keyResponsibilities.map((resp, index) => (
                <li key={index} className="flex items-start gap-2">
                  <div className="mt-1 rounded-full bg-blue-500/20 p-0.5">
                    <List className="w-3 h-3 text-blue-500" />
                  </div>
                  <span className="text-sm">{resp}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-medium mb-2">Benefits</h3>
            <ul className="space-y-1.5">
              {jobDescription.benefits.map((benefit, index) => (
                <li key={index} className="flex items-start gap-2">
                  <div className="mt-1 rounded-full bg-purple-500/20 p-0.5">
                    <List className="w-3 h-3 text-purple-500" />
                  </div>
                  <span className="text-sm">{benefit}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex flex-col sm:flex-row justify-between gap-3 pt-2">
            <button
              onClick={() => setJobDescription(null)}
              className="px-4 py-2 rounded-lg border border-white/10 hover:bg-white/5"
            >
              Generate Another Job Description
            </button>
            <button
              onClick={copyToClipboard}
              className="px-4 py-2 rounded-lg bg-primary text-primary-foreground flex items-center justify-center gap-2"
            >
              <Clipboard className="w-4 h-4" />
              {copied ? 'Copied!' : 'Copy to Clipboard'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobDescriptionGenerator; 