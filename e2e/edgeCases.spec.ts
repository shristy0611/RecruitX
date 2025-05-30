import { test, expect, Page } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import os from 'os';

// Helper function to create a temporary file
async function createTempFile(content: string, extension: string): Promise<string> {
  const tmpdir = os.tmpdir();
  const filename = `temp-${Date.now()}-${Math.random().toString(36).substring(2, 10)}${extension}`;
  const filepath = path.join(tmpdir, filename);
  
  await fs.promises.writeFile(filepath, content);
  return filepath;
}

// Helper function to create an empty file
async function createEmptyFile(extension: string): Promise<string> {
  return createTempFile('', extension);
}

test.describe('Edge Cases and Data Integrity', () => {
  // Test Scenario 5.1: Analysis with Empty Recruiter Notes
  test('should handle analysis with empty recruiter notes', async ({ page }) => {
    // Add a CV without recruiter notes
    await page.goto('/');
    await page.getByRole('button', { name: 'Candidates' }).click();
    await page.getByRole('button', { name: 'Add New Candidate' }).click();

    const cvName = 'CV Without Notes';
    const cvContent = 'This is a CV without any recruiter notes.';

    await page.getByLabel('Candidate Name / Identifier').fill(cvName);
    await page.getByLabel('Paste CV Content').fill(cvContent);
    await page.getByRole('button', { name: 'Add Document' }).click();

    // Add a JD without recruiter notes
    await page.getByRole('button', { name: 'Jobs' }).click();
    await page.getByRole('button', { name: 'Add New Job' }).click();

    const jdTitle = 'JD Without Notes';
    const jdContent = 'This is a JD without any recruiter notes.';

    await page.getByLabel('Job Title / Identifier').fill(jdTitle);
    await page.getByLabel('Paste JD Content').fill(jdContent);
    await page.getByRole('button', { name: 'Add Document' }).click();

    // Perform a match
    await page.getByRole('button', { name: 'Matching' }).click();
    await page.getByText(cvName).click();
    await page.getByText(jdTitle).click();
    await page.getByRole('button', { name: 'Perform Match Analysis' }).click();

    // Wait for the analysis to complete
    await page.waitForSelector('.match-report', { timeout: 60000 });

    // Verify that the match report is displayed
    await expect(page.getByText('Candidate Match Report')).toBeVisible();
    await expect(page.getByText('Overall Match Score')).toBeVisible();
  });

  // Test Scenario 5.2: Analysis with Very Long Recruiter Notes
  test('should handle analysis with very long recruiter notes', async ({ page }) => {
    // Add a CV with very long recruiter notes
    await page.goto('/');
    await page.getByRole('button', { name: 'Candidates' }).click();
    await page.getByRole('button', { name: 'Add New Candidate' }).click();

    const cvName = 'CV With Long Notes';
    const cvContent = 'This is a CV with very long recruiter notes.';
    
    // Generate a long string for recruiter notes
    const longNotes = 'This is a very long recruiter note. '.repeat(100);

    await page.getByLabel('Candidate Name / Identifier').fill(cvName);
    await page.getByLabel('Paste CV Content').fill(cvContent);
    await page.getByLabel('Recruiter Notes (Optional)').fill(longNotes);
    await page.getByRole('button', { name: 'Add Document' }).click();

    // Add a JD with normal notes
    await page.getByRole('button', { name: 'Jobs' }).click();
    await page.getByRole('button', { name: 'Add New Job' }).click();

    const jdTitle = 'JD For Long Notes Test';
    const jdContent = 'This is a JD for testing with long recruiter notes.';

    await page.getByLabel('Job Title / Identifier').fill(jdTitle);
    await page.getByLabel('Paste JD Content').fill(jdContent);
    await page.getByRole('button', { name: 'Add Document' }).click();

    // Perform a match
    await page.getByRole('button', { name: 'Matching' }).click();
    await page.getByText(cvName).click();
    await page.getByText(jdTitle).click();
    await page.getByRole('button', { name: 'Perform Match Analysis' }).click();

    // Wait for the analysis to complete
    await page.waitForSelector('.match-report', { timeout: 90000 }); // Longer timeout for processing long notes

    // Verify that the match report is displayed
    await expect(page.getByText('Candidate Match Report')).toBeVisible();
    await expect(page.getByText('Overall Match Score')).toBeVisible();
  });

  // Test Scenario 5.3: Uploading Invalid File Types
  test('should handle invalid file type uploads gracefully', async ({ page }) => {
    // Create a temporary file with an unsupported extension
    const invalidFilePath = await createTempFile('This is not a supported file type', '.xyz');

    // Try to upload the invalid file
    await page.goto('/');
    await page.getByRole('button', { name: 'Candidates' }).click();
    await page.getByRole('button', { name: 'Add New Candidate' }).click();

    // Listen for the filechooser event
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByLabel('Upload File (.txt, .pdf, .docx, .xlsx)').click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(invalidFilePath);

    // Expect an error message or validation
    // This could be a toast notification, an inline error, etc.
    await expect(page.getByText(/unsupported file type|invalid file format/i)).toBeVisible();
  });

  // Test Scenario 5.4: Uploading Empty Files
  test('should handle empty file uploads gracefully', async ({ page }) => {
    // Create an empty file
    const emptyFilePath = await createEmptyFile('.txt');

    // Try to upload the empty file
    await page.goto('/');
    await page.getByRole('button', { name: 'Candidates' }).click();
    await page.getByRole('button', { name: 'Add New Candidate' }).click();

    // Listen for the filechooser event
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByLabel('Upload File (.txt, .pdf, .docx, .xlsx)').click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(emptyFilePath);

    // Expect an error message or validation
    await expect(page.getByText(/empty file|no content/i)).toBeVisible();
  });

  // Test Scenario 5.5: Attempting Match with No CVs/JDs selected
  test('should disable match button when no CVs/JDs are selected', async ({ page }) => {
    // Navigate to the Matching page
    await page.goto('/');
    await page.getByRole('button', { name: 'Matching' }).click();

    // Verify that the match button is disabled
    await expect(page.getByRole('button', { name: 'Perform Match Analysis' })).toBeDisabled();
  });

  // Test Scenario 5.6: Deleting a CV/JD and ensuring associated reports are gone
  test('should delete associated reports when a CV is deleted', async ({ page }) => {
    // Add a CV
    await page.goto('/');
    await page.getByRole('button', { name: 'Candidates' }).click();
    await page.getByRole('button', { name: 'Add New Candidate' }).click();

    const cvName = 'CV To Delete';
    const cvContent = 'This CV will be deleted to test report cleanup.';

    await page.getByLabel('Candidate Name / Identifier').fill(cvName);
    await page.getByLabel('Paste CV Content').fill(cvContent);
    await page.getByRole('button', { name: 'Add Document' }).click();

    // Add a JD
    await page.getByRole('button', { name: 'Jobs' }).click();
    await page.getByRole('button', { name: 'Add New Job' }).click();

    const jdTitle = 'JD For Deletion Test';
    const jdContent = 'This JD will be used to test report cleanup on CV deletion.';

    await page.getByLabel('Job Title / Identifier').fill(jdTitle);
    await page.getByLabel('Paste JD Content').fill(jdContent);
    await page.getByRole('button', { name: 'Add Document' }).click();

    // Perform a match
    await page.getByRole('button', { name: 'Matching' }).click();
    await page.getByText(cvName).click();
    await page.getByText(jdTitle).click();
    await page.getByRole('button', { name: 'Perform Match Analysis' }).click();

    // Wait for the analysis to complete
    await page.waitForSelector('.match-report', { timeout: 60000 });

    // Go back to Dashboard
    await page.getByRole('button', { name: 'Back to Dashboard' }).click();

    // Verify the report exists in the Dashboard
    await expect(page.getByText(`${cvName} / ${jdTitle}`)).toBeVisible();

    // Delete the CV
    await page.getByRole('button', { name: 'Candidates' }).click();
    
    // Find the delete button associated with this CV and click it
    const deleteButton = page.locator(`tr:has-text("${cvName}") button:has-text("Delete")`);
    await deleteButton.click();
    
    // Confirm deletion if there's a confirmation dialog
    await page.getByRole('button', { name: 'Confirm' }).click();

    // Go back to Dashboard
    await page.getByRole('button', { name: 'Dashboard' }).click();

    // Verify the report is no longer in the Dashboard
    await expect(page.getByText(`${cvName} / ${jdTitle}`)).not.toBeVisible();
  });
}); 