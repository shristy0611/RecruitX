import { test, expect } from '@playwright/test';

test.describe('Bilingual Support', () => {
  test.beforeEach(async ({ page }) => {
    // Set a higher timeout for beforeEach if page loading is slow
    test.setTimeout(60000); // 60 seconds for beforeEach
    await page.goto('/');
  });

  test('should switch UI elements language between English and Japanese', async ({ page }) => {
    test.setTimeout(120000); // 120 seconds for this specific test

    // Check initial language (English)
    // More specific selector for the dashboard heading
    await expect(page.locator('h1.text-2xl.font-semibold')).toHaveText('Recruitment Analytics Dashboard', { timeout: 10000 });
    
    // Navigate to Candidates page to check button text
    await page.getByRole('link', { name: 'Candidates' }).click();
    await expect(page.getByRole('button', { name: 'Add New Candidate' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Bulk Upload CVs' })).toBeVisible();

    // Switch to Japanese
    // Assuming the language switcher is a button that opens a dropdown
    const languageSwitcherButton = page.locator('button#language-switcher'); // Assuming id="language-switcher"
    await languageSwitcherButton.click();
    await page.getByRole('menuitem', { name: '日本語' }).click();
    
    // Wait for language change to apply - increased timeout
    await page.waitForTimeout(2000); 

    // Check UI elements in Japanese
    // Confirm exact Japanese translations from app
    // The navigation links themselves might change
    const dashboardLinkJP = page.getByRole('link', { name: 'ダッシュボード' }); // Dashboard
    await dashboardLinkJP.click();
    await expect(page.locator('h1.text-2xl.font-semibold')).toHaveText('採用分析ダッシュボード'); // Recruitment Analytics Dashboard

    const candidatesLinkJP = page.getByRole('link', { name: '候補者' }); // Candidates
    await candidatesLinkJP.click();
    await expect(page.getByRole('button', { name: '新規候補者追加' })).toBeVisible(); // Add New Candidate
    await expect(page.getByRole('button', { name: 'CV一括アップロード' })).toBeVisible(); // Bulk Upload CVs

    // Switch back to English
    await languageSwitcherButton.click();
    await page.getByRole('menuitem', { name: 'English' }).click();

    await page.waitForTimeout(2000);

    // Check UI elements back in English
    const dashboardLinkEN = page.getByRole('link', { name: 'Dashboard' });
    await dashboardLinkEN.click();
    await expect(page.locator('h1.text-2xl.font-semibold')).toHaveText('Recruitment Analytics Dashboard');
    
    const candidatesLinkEN = page.getByRole('link', { name: 'Candidates' });
    await candidatesLinkEN.click();
    await expect(page.getByRole('button', { name: 'Add New Candidate' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Bulk Upload CVs' })).toBeVisible();
  });

  // Test for AI-generated report language (Simplified)
  test('should generate AI match report in Japanese when language is set to Japanese', async ({ page }) => {
    test.setTimeout(180000); // Longer timeout for AI interaction

    // Setup: Switch to Japanese
    const languageSwitcherButton = page.locator('button#language-switcher');
    await languageSwitcherButton.click();
    await page.getByRole('menuitem', { name: '日本語' }).click();
    await page.waitForTimeout(2000); // wait for language to apply
    
    // Verify dashboard is in Japanese to ensure context
    await page.getByRole('link', { name: 'ダッシュボード' }).click();
    await expect(page.locator('h1.text-2xl.font-semibold')).toHaveText('採用分析ダッシュボード');

    // Add a simple CV (using Japanese for names/content for clarity in test)
    await page.getByRole('link', { name: '候補者' }).click();
    await page.getByRole('button', { name: '新規候補者追加' }).click();
    await page.getByLabel('候補者名またはID').fill('テスト候補者名'); // CV Name
    await page.getByLabel('内容').fill('これは日本語でのCV内容です。候補者はソフトウェア開発の経験があります。'); // CV Content
    await page.getByRole('button', { name: '候補者を追加' }).click(); // Add Candidate
    await expect(page.getByText('テスト候補者名')).toBeVisible({ timeout: 10000 });

    // Add a simple JD
    await page.getByRole('link', { name: '求人' }).click(); // Jobs
    await page.getByRole('button', { name: '新規求人追加' }).click(); // Add New Job
    await page.getByLabel('役職名またはID').fill('テスト役職名'); // Job Title
    await page.getByLabel('内容').fill('これは日本語での職務記述書です。この役職にはプロジェクト管理のスキルが必要です。'); // Job Content
    await page.getByRole('button', { name: '求人を追加' }).click(); // Add Job
    await expect(page.getByText('テスト役職名')).toBeVisible({ timeout: 10000 });

    // Perform match
    await page.getByRole('link', { name: 'マッチング' }).click(); // Matching
    await page.getByLabel('テスト候補者名').check();
    await page.getByLabel('テスト役職名').check();
    await page.getByRole('button', { name: 'マッチング分析を実行' }).click(); // Perform Match Analysis
    
    // Wait for report to be generated and displayed
    // Check for a known Japanese header in the report.
    // This is a key indicator that the report is in Japanese.
    // The exact text "総合的なマッチングスコア" means "Overall Match Score"
    await expect(page.locator('h2').filter({ hasText: '総合的なマッチングスコア' })).toBeVisible({ timeout: 60000 }); // Increased timeout for AI

    // Optionally, check for another Japanese-specific phrase or section title if known
    await expect(page.locator('h3').filter({ hasText: '戦略的洞察' })).toBeVisible(); // "Strategic Insights"
    // Check for a dimension title, assuming "スキル評価" (Skills Assessment) is used and translated
    await expect(page.locator('h4').filter({ hasText: 'スキル評価' })).toBeVisible(); 
  });
});
