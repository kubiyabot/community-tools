export const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const getReadmePreview = (readme?: string): string => {
  if (!readme) return 'No description provided. To add one, include a README.md file in the root folder of the source.';
  
  try {
    // Remove markdown headers
    const withoutHeaders = readme.replace(/#{1,6}\s[^\n]+/g, '');
    
    // Remove markdown links while keeping link text
    const withoutLinks = withoutHeaders.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
    
    // Remove code blocks
    const withoutCode = withoutLinks.replace(/```[\s\S]*?```/g, '');
    
    // Remove inline code
    const withoutInlineCode = withoutCode.replace(/`[^`]+`/g, '');
    
    // Remove special characters and extra whitespace
    const cleaned = withoutInlineCode
      .replace(/[#*~_]/g, '')
      .replace(/\n\s*\n/g, '\n')
      .trim();
    
    // Get first meaningful paragraph (up to 300 chars)
    const firstParagraph = cleaned.split('\n')
      .find(line => line.trim().length > 0) || '';
      
    return firstParagraph.slice(0, 300) + (firstParagraph.length > 300 ? '...' : '');
  } catch (error) {
    console.error('Error parsing README:', error);
    return 'Error parsing README content. Please check the source repository.';
  }
};

export const getTimeAgo = (date?: string): string => {
  if (!date) return 'recently';
  const now = new Date();
  const updated = new Date(date);
  const diff = now.getTime() - updated.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  
  if (days === 0) return 'today';
  if (days === 1) return 'yesterday';
  if (days < 7) return `${days} days ago`;
  if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
  if (days < 365) return `${Math.floor(days / 30)} months ago`;
  return `${Math.floor(days / 365)} years ago`;
}; 