export enum Language {
  EN = 'en',
  JA = 'ja',
}

export type View = 
  | 'dashboard' 
  | 'matching'      // New view for performing matches
  | 'report_details'
  | 'candidates_list'
  | 'candidate_profile'
  | 'jobs_list'
  | 'job_profile'
  | 'settings'
  | 'ai_assistant'  // New AI assistant view with conversational interface
  | 'agents_demo';  // New view to demonstrate all agent types

export type CandidateStatus = 
  | 'ACTIVE_SEEKER' 
  | 'OPEN_TO_OFFERS' 
  | 'PASSIVELY_LOOKING' 
  | 'IN_PROCESS_INTERNAL' 
  | 'NOT_LOOKING' 
  | 'ARCHIVED';

export type JobStatus = 
  | 'OPEN_HIRING' 
  | 'INTERVIEWING' 
  | 'OFFER_EXTENDED' 
  | 'FILLED' 
  | 'ON_HOLD' 
  | 'CLOSED_CANCELLED';

export interface CVData {
  id: string;
  name: string;
  content: string; 
  fileMimeType: string; 
  fileName?: string;
  recruiterNotes?: string;
  createdAt: string; 
  status?: CandidateStatus;
  structuredData?: StructuredCV;
  isStructuring?: boolean; // Added to track background structuring
}

export interface JobDescriptionData {
  id:string;
  title: string;
  content: string; 
  fileMimeType: string; 
  fileName?: string;
  recruiterNotes?: string;
  createdAt: string; 
  status?: JobStatus;
  structuredData?: StructuredJD;
  isStructuring?: boolean; // Added to track background structuring
}

export interface ScoreComponent {
  score: number; // 0-100
  explanation: string;
  details?: string[] | Record<string, unknown>;
}

export interface MatchResult {
  id: string; 
  cvId: string;
  jdId: string;
  overallScore: number; 
  scores: Record<string, ScoreComponent>; 
  detailedExplanation: string;
  positivePoints?: string[];
  painPoints?: string[];
  discussionPoints?: string[];
  timestamp: string;
  reportLanguage: Language;
  candidateName: string; 
  jobTitle: string; 
  cvFileName?: string;
  jdFileName?: string;
  cvRecruiterNotes?: string;
  jdRecruiterNotes?: string;
  appSettingsSnapshot?: AppSettings; 
}

// --- START: Structured Document Types ---
export interface PersonalInformation {
  fullName?: string;
  age?: string;
  sexGender?: string;
  phone?: string; // Professional contact phone
  address?: string; // General location
  email?: string; // Professional email
  linkedin?: string;
  portfolio?: string;
}

export interface WorkExperienceEntry {
  id?: string; // For React keys during editing
  title?: string;
  company?: string;
  dates?: string;
  description?: string; // Can be a list of bullet points or a paragraph
  responsibilities?: string[];
  achievements?: string[];
}

export interface EducationEntry {
  id?: string; // For React keys
  degree?: string;
  institution?: string;
  graduationDate?: string; // Or "Dates Attended"
  details?: string;
}

export interface SkillEntry { // Can be a simple list or categorized
  id?: string; // For React keys
  category?: string; // e.g., "Programming Languages", "Tools", "Soft Skills"
  skills?: string[];
}

export interface ProjectEntry {
  id?: string; // For React keys
  name?: string;
  description?: string;
  technologiesUsed?: string[];
  role?: string;
  dates?: string;
}

export interface StructuredCV {
  personalInfo?: PersonalInformation;
  summary?: string; // or Objective
  workExperience?: WorkExperienceEntry[];
  education?: EducationEntry[];
  skills?: SkillEntry[] | string[]; // Allow for categorized or flat list of skills
  projects?: ProjectEntry[];
  certifications?: string[];
  awards?: string[];
  languages?: string[]; // e.g., "Japanese (Native), English (Business)"
  otherSections?: Record<string, string | string[]>; // For custom sections like "Self PR"
  sourceLanguage?: Language; // To know if regeneration is needed on language switch
}

export interface QualificationEntry { // Can be used for required and preferred
  id?: string; // For React keys
  text: string;
  type?: 'required' | 'preferred' | 'technical' | 'soft'; // Optional categorization
}

export interface ResponsibilityEntry {
  id?: string; // For React keys
  text: string;
}

export interface StructuredJD {
  jobTitle?: string; 
  companyOverview?: string;
  roleSummary?: string; // Or Job Purpose / Overview
  keyResponsibilities?: ResponsibilityEntry[] | string[];
  requiredQualifications?: QualificationEntry[] | string[];
  preferredQualifications?: QualificationEntry[] | string[];
  technicalSkillsRequired?: string[];
  softSkillsRequired?: string[];
  benefits?: string[] | string;
  location?: string;
  salaryRange?: string;
  otherSections?: Record<string, string | string[]>; // For custom sections like "Work Style"
  sourceLanguage?: Language; // To know if regeneration is needed on language switch
}
// --- END: Structured Document Types ---


export interface LocalizedStrings {
  [key: string]: string;
  reportGeneratedInLabel?: string;
  appLanguageIsLabel?: string;
  considerReanalyzingPrompt?: string;
  // Dashboard and Navigation
  dashboardTitle?: string;
  matchingNav?: string; 
  dashboardNav?: string;
  settingsNav?: string; 
  overview?: string;
  cvsManaged?: string;
  jdsManaged?: string;
  analysesPerformed?: string;
  recentAnalyses?: string;
  noRecentAnalyses?: string;
  viewReportButton?: string;
  deleteButton?: string;
  confirmDeleteMessage?: string;
  analysisDate?: string;
  selectReportToView?: string;
  backToDashboard?: string;
  startNewAnalysis?: string; 
  selectCVsAndJDsForMatching?: string; 
  performMatchAnalysisButton?: string; 
  performBulkMatchAnalysisButton?: string; 
  clearSelectionsButton?: string; 

  filterByDimensionCountLabel?: string; 
  filterOptionAllReports?: string;
  filterOption1to3Dimensions?: string;
  filterOption4to6Dimensions?: string;
  filterOption7to10Dimensions?: string;
  noAnalysesWithFilter?: string; 

  // New Dashboard Filters
  filtersSectionTitle?: string;
  filterByScoreThresholdLabel?: string;
  filterByDateRangeLabel?: string;
  filterStartDateLabel?: string;
  filterEndDateLabel?: string;
  clearDateFilterButton?: string;
  noAnalysesWithScoreDateFilter?: string; 

  // Candidate & Job Management
  candidatesNav?: string;
  jobsNav?: string;
  candidateProfileTitle?: string;
  jobProfileTitle?: string;
  editCandidateProfileTitle?: string;
  editJobProfileTitle?: string;
  saveChangesButton?: string;
  cancelButton?: string;
  replaceFileButton?: string;
  allCandidatesTitle?: string;
  allJobsTitle?: string;
  noCandidatesManaged?: string;
  noJobsManaged?: string;
  addDocumentButton?: string; 
  addCandidateButton?: string; 
  addJobButton?: string; 
  addNewCandidateTitle?: string; 
  addNewJobTitle?: string; 
  viewEditProfileButton?: string;
  contentNonEditable?: string;
  confirmDeleteCandidateMessage?: string;
  confirmDeleteJobMessage?: string;
  documentStatusLabel?: string; 
  filterByStatusLabel?: string; 
  statusAll?: string; 
  // Candidate Statuses
  statusCandidateActiveSeeker?: string; 
  statusCandidateOpenToOffers?: string; 
  statusCandidatePassivelyLooking?: string; 
  statusCandidateInProcessInternal?: string; 
  statusCandidateNotLooking?: string; 
  statusCandidateArchived?: string; 
  // Job Statuses
  statusJobOpenHiring?: string; 
  statusJobInterviewing?: string; 
  statusJobOfferExtended?: string; 
  statusJobFilled?: string; 
  statusJobOnHold?: string; 
  statusJobClosedCancelled?: string; 
  noCandidatesWithStatusFilter?: string; 
  noJobsWithStatusFilter?: string; 
  // File handling
  errorUnsupportedFileType?: string;
  errorFileSizeTooLarge?: string;
  errorParsingFile?: string;
  processingFile?: string;
  // Caching & Progress
  cacheHitMessage?: string;
  analysisProgressMessage?: string;
  // Settings Page
  settingsTitle?: string;
  assessmentDimensionsSectionTitle?: string;
  dimensionProcessingTimeWarning?: string; 
  addDimensionButton?: string;
  dimensionLabelLabel?: string;
  dimensionLabelPlaceholder?: string;
  dimensionPromptGuidanceLabel?: string;
  dimensionPromptGuidancePlaceholder?: string;
  dimensionIsActiveLabel?: string;
  dimensionIsDefaultLabel?: string;
  confirmDeleteDimensionMessage?: string;
  rankingDisplaySettingsSectionTitle?: string; 
  nexusRankingScoreThresholdLabel?: string; 
  nexusRankingScoreThresholdDescription?: string; 
  saveSettingsButton?: string;
  resetSettingsButton?: string;
  settingsSavedSuccess?: string;
  settingsResetSuccess?: string;
  errorMinDimensions?: string;
  // Nexus Ranking
  topCandidateMatchesTitle?: string;
  bestJobFitsTitle?: string;
  jumpToProfileButton?: string;
  viewFullAnalysisButton?: string;
  nexusScanPendingMessage?: string;
  noMatchesYet?: string;
  noMatchesAboveThresholdMessage?: string; 
  // New Report Sections
  keyStrengthsTitle?: string;
  areasForClarificationTitle?: string;
  strategicDiscussionPointsTitle?: string;
  // Structured View
  structuredOverviewTitle?: string; 
  refreshStructuredViewButton?: string;
  structuringDocumentMessage?: string; 
  structuredViewDisclaimer?: string;
  failedToGenerateStructuredViewMessage?: string;
  editButtonLabel?: string;
  doneButtonLabel?: string;
  addNewEntryButtonLabel?: string;
  confirmDeleteEntryMessage?: string;
  noEntriesFound?: string; 
  // Structured CV Sections
  cvSectionPersonalInfo?: string;
  cvFieldFullName?: string;
  cvFieldAge?: string;
  cvFieldSexGender?: string;
  cvFieldPhone?: string;
  cvFieldAddress?: string;
  cvFieldEmail?: string;
  cvFieldLinkedIn?: string;
  cvFieldPortfolio?: string;
  cvSectionSummary?: string;
  cvSectionWorkExperience?: string;
  cvFieldJobTitle?: string;
  cvFieldCompany?: string;
  cvFieldDates?: string;
  cvFieldDescription?: string;
  cvFieldResponsibilities?: string;
  cvFieldAchievements?: string;
  cvSectionEducation?: string;
  cvFieldDegree?: string;
  cvFieldInstitution?: string;
  cvFieldGraduationDate?: string;
  cvFieldEduDetails?: string;
  cvSectionSkills?: string;
  cvFieldSkillCategory?: string;
  cvFieldSkillsList?: string;
  cvSectionProjects?: string;
  cvFieldProjectName?: string;
  cvFieldProjectDescription?: string;
  cvFieldTechnologiesUsed?: string;
  cvFieldProjectRole?: string;
  cvFieldProjectDates?: string;
  cvSectionCertifications?: string;
  cvSectionAwards?: string;
  cvSectionLanguages?: string;
  // Structured JD Sections
  jdFieldJobTitle?: string;
  jdSectionCompanyOverview?: string;
  jdSectionRoleSummary?: string;
  jdSectionKeyResponsibilities?: string;
  jdSectionRequiredQualifications?: string;
  jdSectionPreferredQualifications?: string;
  jdSectionTechnicalSkills?: string;
  jdSectionSoftSkills?: string;
  jdSectionBenefits?: string;
  jdSectionLocation?: string;
  jdSectionSalary?: string;
  jdSectionOther?: string;
  // Simple Document Form
  documentNameLabel?: string;
  documentTitleLabel?: string;
  documentNamePlaceholder?: string;
  documentTitlePlaceholder?: string;
  pasteOrUploadLabel?: string;
  uploadButtonLabel?: string;
  contentPlaceholder?: string;
  notesPlaceholder?: string;
  documentAddedSuccess?: string;
  genericSaveError?: string;
  isStructuringMessage?: string;

  // AI Methodology Section
  aiMethodologySectionTitle?: string;
  aiMethodologyIntro?: string;
  aiMethodologyPointEvidenceTitle?: string;
  aiMethodologyPointEvidenceDetail?: string;
  aiMethodologyPointNotesTitle?: string;
  aiMethodologyPointNotesDetail?: string;
  aiMethodologyPointFairnessTitle?: string;
  aiMethodologyPointFairnessDetail?: string;
  aiMethodologyPointStructuredTitle?: string;
  aiMethodologyPointStructuredDetail?: string;
  aiMethodologyPointHumanExpertiseTitle?: string;
  aiMethodologyPointHumanExpertiseDetail?: string;
}

export interface AppTranslations {
  [Language.EN]: LocalizedStrings;
  [Language.JA]: LocalizedStrings;
}

export interface GeminiAnalysisResponse {
  candidateName?: string;
  jobTitle?: string;
  scores: Record<string, ScoreComponent>; 
  overallScore: number;
  detailedExplanation: string;
  positivePoints?: string[];
  painPoints?: string[];
  discussionPoints?: string[];
}

export interface GroundingChunkWeb {
  uri: string;
  title: string;
}

export interface GroundingChunk {
  web: GroundingChunkWeb;
}
export interface GroundingMetadata {
    groundingChunks?: GroundingChunk[];
}

export interface CachedAnalysisItem {
  timestamp: number;
  geminiResponse: GeminiAnalysisResponse;
  appSettingsSnapshot?: AppSettings; 
}


export interface AnalysisProgressProps {
  progress: number;
}

// Settings specific types
export interface AssessmentDimensionSetting {
  id: string; 
  label: string; 
  promptGuidance: string; 
  isActive: boolean; 
  isDefault?: boolean; 
}

export interface AppSettings {
  assessmentDimensions: AssessmentDimensionSetting[];
  nexusRankingScoreThreshold: number; 
}
