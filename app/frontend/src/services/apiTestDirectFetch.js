// Simple direct API test using fetch (no axios)
const apiTestDirectFetch = {
  testDirectHealth: async () => {
    try {
      const response = await fetch('http://localhost:8000/health');
      const data = await response.json();
      console.log('Direct Health Response:', data);
      return data;
    } catch (error) {
      console.error('Direct Health Error:', error);
      throw error;
    }
  },

  testProxiedHealth: async () => {
    try {
      const response = await fetch('/api/health');
      const data = await response.json();
      console.log('Proxied Health Response:', data);
      return data;
    } catch (error) {
      console.error('Proxied Health Error:', error);
      throw error;
    }
  }
};

// Run tests if loaded directly
if (typeof window !== 'undefined') {
  console.log('Running direct API tests...');
  apiTestDirectFetch.testDirectHealth().catch(err => console.error('Direct test failed:', err));
  apiTestDirectFetch.testProxiedHealth().catch(err => console.error('Proxied test failed:', err));
}

export default apiTestDirectFetch; 