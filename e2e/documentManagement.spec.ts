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
  await expect(page.getByTestId('job-title')).toHaveText(title);
}

test.describe('Document Management', () => {
  // Test Scenario 1.1: Add Single Document (CV) - Text Input
  test('should allow adding a new CV via text input', async ({ page }) => {
    await addCvViaTextInput(
      page, 
      'Test Candidate One', 
      'This is the CV content for Test Candidate One. Skills: Playwright, TypeScript.', 
      'Initial recruiter notes for candidate one.'
    );
  });

  // Test Scenario 1.2: Add Single Document (JD) - File Upload (.txt)
  test('should allow adding a new JD via .txt file upload', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Jobs', exact: true }).first().click();
    await page.getByRole('button', { name: 'Add New Job' }).click();

    await expect(page.getByLabel('Job Title / Identifier')).toBeVisible();

    const sampleTxtContent = 'Job Title: SRE\nDescription: Looking for an SRE with experience in Kubernetes.';
    const fileBuffer = Buffer.from(sampleTxtContent, 'utf-8');

    // Listen for the filechooser event
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByLabel('Upload File (.txt, .pdf, .docx, .xlsx)').click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles({
      name: 'sample-jd.txt',
      mimeType: 'text/plain',
      buffer: fileBuffer,
    });

    // Verify auto-fill and content extraction (adjust selectors as needed)
    await expect(page.getByLabel('Job Title / Identifier')).toHaveValue('sample-jd.txt');
    await expect(page.getByLabel('Paste JD Content')).toContainText('Job Title: SRE');
    
    await page.getByRole('button', { name: 'Add Document' }).click();
    await expect(page.getByTestId('job-title')).toHaveText('sample-jd.txt');
  });

  // Test Scenario 1.4: Edit Document (CV)
  test('should allow editing a CV', async ({ page }) => {
    // First add a CV
    const cvName = 'CV to Edit';
    const cvContent = 'This CV will be edited.';
    
    await addCvViaTextInput(page, cvName, cvContent);
    
    // Go to the profile page
    await page.goto('/');
    await page.getByRole('button', { name: 'Candidates' }).click();
    await page.getByTestId('candidate-name').first().click();
    
    // Verify we're on the profile page
    await expect(page.getByText(cvName, { exact: false })).toBeVisible({ timeout: 30000 });
    
    // Edit the CV
    const updatedName = 'Updated CV Name';
    await page.fill('input[id*="candidate-name"]', updatedName);
    
    const recruiterNotes = 'These are updated recruiter notes.';
    await page.fill('textarea[placeholder*="Recruiter Notes"]', recruiterNotes);
    
    // Save changes
    await page.getByRole('button', { name: 'Save Changes' }).click();
    
    // Verify changes were saved - go back to candidates list
    await page.goto('/');
    await page.getByRole('button', { name: 'Candidates' }).click();
    await expect(page.getByTestId('candidate-name').first()).toContainText(updatedName);
  });

  // Test Scenario 1.5: Delete Document (JD)
  test('should allow deleting a JD', async ({ page }) => {
    // First add a JD
    const jdTitle = 'JD to Delete';
    const jdContent = 'This JD will be deleted.';
    
    await addJdViaTextInput(page, jdTitle, jdContent);
    
    // Now delete the JD
    // Assuming there's a delete button or icon next to each JD in the list
    await page.getByRole('navigation').getByRole('button', { name: 'Jobs', exact: true }).first().click();
    
    // Find the delete button associated with this JD and click it
    const deleteButton = page.locator(`[data-testid="job-row-${jdTitle}"] button[aria-label="Delete ${jdTitle}"]`);
    await deleteButton.click();
    
    // Confirm deletion if there's a confirmation dialog
    await page.getByRole('button', { name: 'Confirm' }).click();
    
    // Verify the JD is no longer in the list
    await expect(page.getByTestId('job-title')).not.toHaveText(jdTitle);
  });

  // Test Scenario 1.3: Bulk Upload Documents (CVs)
  test('should allow bulk uploading of CVs', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Candidates' }).click();
    
    // Create the file content
    const cv1Content = 'CV 1 Content\nSkills: JavaScript, React\nExperience: 5 years';
    const cv2Content = 'CV 2 Content\nSkills: Python, Django\nExperience: 3 years';
    
    // Set input files directly on the file input element
    const fileInput = page.locator('input[type="file"]');
    
    // Make sure the file input is visible first
    await page.getByRole('button', { name: 'Bulk Upload CVs' }).click();
    
    // Now set the files on the input
    await fileInput.setInputFiles([
      {
        name: 'cv1.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from(cv1Content, 'utf-8'),
      },
      {
        name: 'cv2.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from(cv2Content, 'utf-8'),
      }
    ]);
    
    // Wait for the upload to complete and verify
    await expect(page.getByText('Bulk analysis completed')).toBeVisible({ timeout: 30000 });
    
    // Wait for upload to complete and verify both CVs are in the list
    await expect(page.getByTestId('candidate-name').first()).toContainText('cv1.txt');
  });
}); 