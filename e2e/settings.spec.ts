import { test, expect } from '@playwright/test';

test.describe('Settings Functionality', () => {
  // Test Scenario 3.1: Modify Assessment Dimensions
  test('should allow modifying assessment dimensions', async ({ page }) => {
    // Navigate to Settings page
    await page.goto('/');
    await page.getByRole('button', { name: 'Settings' }).click();
    
    // Wait for settings page to load
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
    
    // Find a dimension to deactivate (assuming there's at least one active dimension)
    // This selector might need adjustment based on your actual UI
    const firstActiveDimension = page.locator('.assessment-dimension.active').first();
    const dimensionName = await firstActiveDimension.locator('.dimension-name').textContent();
    
    // Toggle the dimension off
    await firstActiveDimension.locator('input[type="checkbox"]').click();
    
    // Edit AI prompt guidance for another dimension
    const secondDimension = page.locator('.assessment-dimension').nth(1);
    const promptTextarea = secondDimension.locator('textarea');
    const originalPrompt = await promptTextarea.inputValue();
    const newPrompt = originalPrompt + ' - Modified for testing';
    
    await promptTextarea.fill(newPrompt);
    
    // Save settings
    await page.getByRole('button', { name: 'Save All Settings' }).click();
    
    // Verify settings were saved (look for a success message or indicator)
    await expect(page.getByText('Settings saved successfully')).toBeVisible();
    
    // Reload the page to verify persistence
    await page.reload();
    
    // Verify the dimension is still deactivated
    await expect(page.locator(`.assessment-dimension:has-text("${dimensionName}") input[type="checkbox"]`)).not.toBeChecked();
    
    // Verify the prompt guidance was saved
    await expect(secondDimension.locator('textarea')).toHaveValue(newPrompt);
  });

  // Test Scenario 3.2: Modify Nexus Ranking Score Threshold
  test('should allow modifying the nexus ranking score threshold', async ({ page }) => {
    // Navigate to Settings page
    await page.goto('/');
    await page.getByRole('button', { name: 'Settings' }).click();
    
    // Find the nexus ranking threshold input
    const thresholdInput = page.getByLabel('Nexus Ranking Score Threshold');
    
    // Get the current value
    const currentValue = await thresholdInput.inputValue();
    
    // Set a new value
    const newValue = '75'; // Assuming the valid range is 0-100
    await thresholdInput.fill(newValue);
    
    // Save settings
    await page.getByRole('button', { name: 'Save All Settings' }).click();
    
    // Verify settings were saved
    await expect(page.getByText('Settings saved successfully')).toBeVisible();
    
    // Reload the page to verify persistence
    await page.reload();
    
    // Verify the new threshold value persisted
    await expect(thresholdInput).toHaveValue(newValue);
  });

  // Test Scenario 3.3: Reset Settings to Default
  test('should allow resetting settings to default', async ({ page }) => {
    // Navigate to Settings page
    await page.goto('/');
    await page.getByRole('button', { name: 'Settings' }).click();
    
    // Make some changes first
    // Change nexus ranking threshold
    const thresholdInput = page.getByLabel('Nexus Ranking Score Threshold');
    await thresholdInput.fill('80');
    
    // Toggle a dimension
    const someDimension = page.locator('.assessment-dimension').first();
    const checkbox = someDimension.locator('input[type="checkbox"]');
    const isChecked = await checkbox.isChecked();
    await checkbox.click(); // Toggle the current state
    
    // Click reset to defaults
    await page.getByRole('button', { name: 'Reset to Defaults' }).click();
    
    // Confirm reset if there's a confirmation dialog
    const confirmButton = page.getByRole('button', { name: 'Confirm' });
    if (await confirmButton.isVisible()) {
      await confirmButton.click();
    }
    
    // Save settings
    await page.getByRole('button', { name: 'Save All Settings' }).click();
    
    // Verify settings were saved
    await expect(page.getByText('Settings saved successfully')).toBeVisible();
    
    // Reload the page
    await page.reload();
    
    // Verify the settings are back to default
    // This assumes that the default nexus ranking threshold is 70
    await expect(thresholdInput).toHaveValue('70');
    
    // Verify the dimension checkbox is back to its default state
    // This assumes that all dimensions are active by default
    await expect(checkbox).toBeChecked();
  });
}); 