import { test, expect, Page } from '@playwright/test';

// Helper function to add a CV via text input
async function addCvViaTextInput(page: Page, name: string, content: string, notes: string = '') {
  await page.goto('/');
  await page.getByRole('button', { name: 'Candidates' }).click();
  await page.getByRole('button', { name: 'Add New Candidate' }).click();

  await expect(page.getByLabel('Candidate Name / Identifier')).toBeVisible();
  await page.getByLabel('Candidate Name / Identifier').fill(name);
  await page.getByLabel('Paste CV Content').fill(content);
  
  if (notes) {
    await page.getByLabel('Recruiter Notes (Optional)').fill(notes);
  }
  
  await page.getByRole('button', { name: 'Add Document' }).click();
  await expect(page.getByTestId('candidate-name').first()).toHaveText(name);
}

// Helper function to add a JD via text input
async function addJdViaTextInput(page: Page, title: string, content: string, notes: string = '') {
  await page.goto('/');
  await page.getByRole('button', { name: 'Jobs', exact: true }).first().click();
  await page.getByRole('button', { name: 'Add New Job' }).click();

  await expect(page.getByLabel('Job Title / Identifier')).toBeVisible();
  await page.getByLabel('Job Title / Identifier').fill(title);
  await page.getByLabel('Paste JD Content').fill(content);
  
  if (notes) {
    await page.getByLabel('Recruiter Notes (Optional)').fill(notes);
  }
  
  await page.getByRole('button', { name: 'Add Document' }).click();
  await expect(page.getByTestId(`job-profile-title-${title}`)).toHaveText(title);
}

test.describe('Matching Functionality', () => {
  // Test Scenario 2.1: Single CV - Single JD Match
  test('should perform a single CV to single JD match analysis', async ({ page }) => {
    // Add a sample CV
    const cvName = 'Software Engineer CV';
    const cvContent = `
      John Doe
      Software Engineer with 5 years of experience
      
      SKILLS:
      - JavaScript, TypeScript, React, Node.js
      - AWS, Docker, Kubernetes
      - CI/CD, Test Automation
      
      EXPERIENCE:
      Tech Company Inc. (2018-2023)
      - Developed and maintained web applications using React
      - Implemented microservices using Node.js
      - Automated deployment processes with CI/CD pipelines
    `;
    const cvNotes = 'Strong candidate with good cloud experience';
    
    await addCvViaTextInput(page, cvName, cvContent, cvNotes);
    
    // Add a sample JD
    const jdTitle = 'Senior Frontend Developer';
    const jdContent = `
      We are looking for a Senior Frontend Developer with:
      
      REQUIREMENTS:
      - 3+ years of experience with React
      - Strong TypeScript skills
      - Experience with modern frontend tooling
      - Knowledge of CI/CD practices
      
      RESPONSIBILITIES:
      - Develop and maintain web applications
      - Collaborate with backend developers
      - Mentor junior developers
    `;
    const jdNotes = 'We need someone who can start immediately';
    
    await addJdViaTextInput(page, jdTitle, jdContent, jdNotes);
    
    // Navigate to the Matching page
    await page.goto('/');
    await page.getByRole('button', { name: 'Matching' }).click();
    
    // Select the CV and JD
    await page.getByTestId('candidate-name', { hasText: cvName }).first().click();
    await page.getByTestId('job-title', { hasText: jdTitle }).first().click();
    
    // Perform the match analysis
    await page.getByRole('button', { name: 'Perform Match Analysis' }).click();
    
    // Wait for the analysis to complete (this might take some time due to AI processing)
    // You might need to adjust the timeout if the AI processing takes longer
    await page.waitForSelector('.match-report', { timeout: 60000 });
    
    // Verify that the match report is displayed
    await expect(page.getByText('Candidate Match Report')).toBeVisible();
    await expect(page.getByText('Overall Match Score')).toBeVisible();
    
    // Verify that the candidate and job names are displayed in the report
    await expect(page.getByTestId('candidate-name').first()).toHaveText(cvName);
    await expect(page.getByTestId('job-title').first()).toHaveText(jdTitle);
  });

  // Test Scenario 2.2: Bulk Match Analysis
  test('should perform a bulk match analysis with multiple CVs and one JD', async ({ page }) => {
    // Add multiple CVs
    const cv1Name = 'Frontend Developer CV';
    const cv1Content = `
      Jane Smith
      Frontend Developer with 3 years of experience
      
      SKILLS:
      - JavaScript, React, CSS
      - Responsive Design
      - UI/UX principles
      
      EXPERIENCE:
      Web Agency (2020-2023)
      - Developed responsive web applications
      - Implemented UI designs using React
      - Collaborated with UX designers
    `;
    
    const cv2Name = 'Backend Developer CV';
    const cv2Content = `
      Mike Johnson
      Backend Developer with 4 years of experience
      
      SKILLS:
      - Node.js, Express, MongoDB
      - RESTful APIs
      - Docker, AWS
      
      EXPERIENCE:
      Tech Solutions (2019-2023)
      - Developed microservices using Node.js
      - Designed and implemented RESTful APIs
      - Managed AWS infrastructure
    `;
    
    await addCvViaTextInput(page, cv1Name, cv1Content);
    await addCvViaTextInput(page, cv2Name, cv2Content);
    
    // Add a JD
    const jdTitle = 'Full Stack Developer';
    const jdContent = `
      We are looking for a Full Stack Developer with:
      
      REQUIREMENTS:
      - Experience with React and Node.js
      - Knowledge of database systems
      - Understanding of cloud services
      
      RESPONSIBILITIES:
      - Develop both frontend and backend components
      - Collaborate with the product team
      - Maintain existing applications
    `;
    
    await addJdViaTextInput(page, jdTitle, jdContent);
    
    // Navigate to the Matching page
    await page.goto('/');
    await page.getByRole('button', { name: 'Matching' }).click();
    
    // Select multiple CVs and the JD
    await page.getByTestId('candidate-name', { hasText: cv1Name }).first().click();
    await page.getByTestId('candidate-name', { hasText: cv2Name }).first().click();
    await page.getByTestId('job-title', { hasText: jdTitle }).first().click();
    
    // Perform the bulk match analysis
    await page.getByRole('button', { name: 'Perform Bulk Match Analysis' }).click();
    
    // Wait for the analysis to complete and check for success message
    await expect(page.getByText('Bulk analysis completed')).toBeVisible({ timeout: 120000 });
    
    // Navigate to Dashboard to check for the reports
    await page.getByRole('button', { name: 'Dashboard' }).click();
    
    // Verify that both match reports are listed in the Dashboard
    await expect(page.getByTestId('candidate-name').first()).toContainText(cv1Name);
    await expect(page.getByTestId('candidate-name').nth(1)).toContainText(cv2Name);
    await expect(page.getByTestId('job-title').first()).toHaveText(jdTitle);
  });

  // Test Scenario 2.3: View Match Report from Dashboard
  test('should allow viewing a match report from the Dashboard', async ({ page }) => {
    // First create a CV and JD and perform a match
    const cvName = 'Data Scientist CV';
    const cvContent = `
      Alice Brown
      Data Scientist with 6 years of experience
      
      SKILLS:
      - Python, R, SQL
      - Machine Learning, Deep Learning
      - Data Visualization
      
      EXPERIENCE:
      Data Insights Inc. (2017-2023)
      - Developed predictive models
      - Analyzed large datasets
      - Created data visualization dashboards
    `;
    
    const jdTitle = 'Senior Data Scientist';
    const jdContent = `
      We are looking for a Senior Data Scientist with:
      
      REQUIREMENTS:
      - 5+ years of experience in data science
      - Proficiency in Python and SQL
      - Experience with machine learning algorithms
      
      RESPONSIBILITIES:
      - Develop and deploy machine learning models
      - Analyze complex datasets
      - Present findings to stakeholders
    `;
    
    await addCvViaTextInput(page, cvName, cvContent);
    await addJdViaTextInput(page, jdTitle, jdContent);
    
    // Perform a match
    await page.goto('/');
    await page.getByRole('button', { name: 'Matching' }).click();
    await page.getByTestId('candidate-name', { hasText: cvName }).click();
    await page.getByTestId('job-title', { hasText: jdTitle }).click();
    await page.getByRole('button', { name: 'Perform Match Analysis' }).click();
    
    // Wait for the analysis to complete
    await page.waitForSelector('.match-report', { timeout: 60000 });
    
    // Go back to Dashboard
    await page.getByRole('button', { name: 'Back to Dashboard' }).click();
    
    // Find and click on the match report in the Dashboard
    await page.getByTestId('candidate-name', { hasText: cvName }).click();
    
    // Verify the match report is displayed
    await expect(page.getByText('Candidate Match Report')).toBeVisible();
    await expect(page.getByTestId('candidate-name')).toHaveText(cvName);
    await expect(page.getByTestId('job-title')).toHaveText(jdTitle);
  });
}); 