import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('/');
  
  // Wait for the page to load
  await page.waitForLoadState('networkidle');
  
  // Check if the page has the correct title
  await expect(page).toHaveTitle(/RecruitX/);
});

test('has navigation buttons', async ({ page }) => {
  await page.goto('/');
  
  // Wait for the page to load
  await page.waitForLoadState('networkidle');
  
  // Check if the navigation buttons are visible
  await expect(page.getByRole('button', { name: 'Dashboard' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Matching' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Candidates' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Jobs' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Settings' })).toBeVisible();
});

test('can navigate to different pages', async ({ page }) => {
  await page.goto('/');
  
  // Wait for the page to load
  await page.waitForLoadState('networkidle');
  
  // Navigate to Candidates page
  await page.getByRole('button', { name: 'Candidates' }).click();
  await expect(page.getByRole('heading', { name: 'All Candidates' })).toBeVisible();
  
  // Navigate to Jobs page
  await page.getByRole('button', { name: 'Jobs' }).click();
  await expect(page.getByRole('heading', { name: 'All Jobs' })).toBeVisible();
  
  // Navigate to Settings page
  await page.getByRole('button', { name: 'Settings' }).click();
  await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
  
  // Navigate back to Dashboard
  await page.getByRole('button', { name: 'Dashboard' }).click();
  await expect(page.getByText('System Overview')).toBeVisible();
});
