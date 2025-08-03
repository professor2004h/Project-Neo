/**
 * Demo script to showcase the new extension features
 * This script demonstrates the enhanced content analysis, bookmark system, and related resources
 */

// Demo: Enhanced Content Analysis
function demoContentAnalysis() {
  console.log('=== Enhanced Content Analysis Demo ===');
  
  const mockContent = {
    title: 'Understanding Fractions - Primary Mathematics',
    headings: [
      { text: 'What are Fractions?', level: 1 },
      { text: 'Adding Fractions', level: 2 },
      { text: 'Subtracting Fractions', level: 2 }
    ],
    paragraphs: [
      { text: 'A fraction represents a part of a whole number. When we divide something into equal parts, each part is a fraction.' },
      { text: 'To add fractions with the same denominator, we add the numerators and keep the denominator the same.' }
    ],
    mathContent: [
      { content: '1/2 + 1/4 = 2/4 + 1/4 = 3/4' },
      { content: '3/5 - 1/5 = 2/5' }
    ],
    vocabulary: [
      { term: 'numerator' },
      { term: 'denominator' },
      { term: 'fraction' }
    ]
  };

  const url = 'https://www.mathsisfun.com/fractions.html';

  // Simulate the enhanced local analysis
  const analysis = performLocalAnalysis(mockContent, url);
  
  console.log('Content Analysis Result:', analysis);
  console.log('✓ Educational content detected:', analysis.educational);
  console.log('✓ Subject identified:', analysis.subject);
  console.log('✓ Level determined:', analysis.level);
  console.log('✓ Topics extracted:', analysis.topics);
  console.log('✓ Confidence score:', analysis.confidence);
  console.log('');
}

// Demo: Bookmark System
function demoBookmarkSystem() {
  console.log('=== Bookmark System Demo ===');
  
  const mockBookmarks = [];
  
  // Demo adding bookmarks
  const pages = [
    {
      url: 'https://www.cambridge.org/fractions',
      title: 'Understanding Fractions',
      subject: 'mathematics',
      level: 'primary',
      topics: ['fractions', 'basic arithmetic'],
      timestamp: new Date().toISOString(),
      favicon: 'https://www.cambridge.org/favicon.ico'
    },
    {
      url: 'https://www.bbc.co.uk/bitesize/science',
      title: 'BBC Science for Kids',
      subject: 'science',
      level: 'primary',
      topics: ['plants', 'animals', 'experiments'],
      timestamp: new Date().toISOString(),
      favicon: 'https://www.bbc.co.uk/favicon.ico'
    },
    {
      url: 'https://learnenglishkids.britishcouncil.org/pronunciation',
      title: 'English Pronunciation Practice',
      subject: 'esl',
      level: 'primary',
      topics: ['pronunciation', 'phonics', 'speaking'],
      timestamp: new Date().toISOString(),
      favicon: 'https://learnenglishkids.britishcouncil.org/favicon.ico'
    }
  ];

  pages.forEach(page => {
    mockBookmarks.unshift(page);
    console.log(`✓ Added bookmark: ${page.title} (${page.subject})`);
  });

  console.log(`Total bookmarks: ${mockBookmarks.length}`);
  
  // Demo bookmark filtering by subject
  const mathBookmarks = mockBookmarks.filter(b => b.subject === 'mathematics');
  const scienceBookmarks = mockBookmarks.filter(b => b.subject === 'science');
  const eslBookmarks = mockBookmarks.filter(b => b.subject === 'esl');
  
  console.log(`Mathematics bookmarks: ${mathBookmarks.length}`);
  console.log(`Science bookmarks: ${scienceBookmarks.length}`);
  console.log(`ESL bookmarks: ${eslBookmarks.length}`);
  
  // Demo bookmark limit enforcement
  const manyBookmarks = Array.from({ length: 55 }, (_, i) => ({
    url: `https://example.com/page${i}`,
    title: `Educational Page ${i}`,
    subject: 'general',
    level: 'primary'
  }));
  
  const limitedBookmarks = manyBookmarks.slice(0, 50);
  console.log(`✓ Bookmark limit enforced: ${limitedBookmarks.length}/50 bookmarks saved`);
  console.log('');
}

// Demo: Related Resources System
function demoRelatedResources() {
  console.log('=== Related Resources System Demo ===');
  
  const contexts = [
    { subject: 'mathematics', level: 'primary', topics: ['fractions', 'decimals'] },
    { subject: 'science', level: 'primary', topics: ['plants', 'animals'] },
    { subject: 'esl', level: 'primary', topics: ['pronunciation', 'vocabulary'] }
  ];

  contexts.forEach(context => {
    const resources = getFallbackResources(context);
    console.log(`\n${context.subject.toUpperCase()} Resources:`);
    resources.resources.forEach((resource, index) => {
      console.log(`  ${index + 1}. ${resource.title}`);
      console.log(`     ${resource.description}`);
      console.log(`     Type: ${resource.type} | Level: ${resource.level}`);
    });
  });
  console.log('');
}

// Demo: Widget Tab System
function demoTabSystem() {
  console.log('=== Widget Tab System Demo ===');
  
  const tabs = ['chat', 'bookmarks', 'resources'];
  let activeTab = 'chat';
  
  console.log(`Initial active tab: ${activeTab}`);
  
  tabs.forEach(tab => {
    activeTab = tab;
    console.log(`✓ Switched to ${tab} tab`);
    
    // Simulate tab-specific content loading
    switch (tab) {
      case 'bookmarks':
        console.log('  → Loading bookmarks list...');
        console.log('  → Found 3 educational bookmarks');
        break;
      case 'resources':
        console.log('  → Loading related resources...');
        console.log('  → Found 4 relevant educational resources');
        break;
      case 'chat':
        console.log('  → AI tutor ready for questions');
        break;
    }
  });
  console.log('');
}

// Helper functions (simplified versions of the actual implementation)
function performLocalAnalysis(content, url) {
  const analysis = {
    educational: false,
    subject: null,
    level: null,
    topics: [],
    difficulty: 'unknown',
    language: 'en',
    confidence: 0
  };

  // Educational domain detection
  const educationalDomains = {
    'cambridge.org': { subject: 'general', level: 'primary', confidence: 0.9 },
    'bbc.co.uk/bitesize': { subject: 'general', level: 'primary', confidence: 0.9 },
    'mathsisfun.com': { subject: 'mathematics', level: 'primary', confidence: 0.8 }
  };

  // Check domain
  for (const [domain, info] of Object.entries(educationalDomains)) {
    if (url.includes(domain)) {
      analysis.educational = true;
      analysis.subject = info.subject;
      analysis.level = info.level;
      analysis.confidence = info.confidence;
      break;
    }
  }

  // Content-based analysis
  const titleText = content.title.toLowerCase();
  const allText = content.paragraphs.map(p => p.text).join(' ').toLowerCase();
  
  // Subject detection patterns
  const subjectPatterns = {
    mathematics: ['math', 'fraction', 'arithmetic', 'algebra', 'geometry', 'number'],
    science: ['science', 'biology', 'chemistry', 'physics', 'experiment'],
    english: ['english', 'grammar', 'vocabulary', 'reading', 'writing'],
    esl: ['esl', 'pronunciation', 'phonics', 'speaking', 'listening']
  };

  // Check for subject patterns
  let maxSubjectScore = 0;
  let detectedSubject = null;

  for (const [subject, patterns] of Object.entries(subjectPatterns)) {
    const score = patterns.reduce((count, pattern) => {
      const titleMatches = (titleText.match(new RegExp(pattern, 'g')) || []).length * 2;
      const textMatches = (allText.match(new RegExp(pattern, 'g')) || []).length;
      return count + titleMatches + textMatches;
    }, 0);

    if (score > maxSubjectScore) {
      maxSubjectScore = score;
      detectedSubject = subject;
    }
  }

  if (maxSubjectScore > 3 || content.mathContent?.length > 0) {
    analysis.educational = true;
    analysis.subject = detectedSubject || 'general';
    analysis.confidence = Math.min(0.9, maxSubjectScore / 10);
  }

  // Extract topics from headings
  if (analysis.educational) {
    analysis.topics = content.headings
      .filter(h => h.text.length > 5 && h.text.length < 100)
      .map(h => h.text.trim())
      .slice(0, 5);
  }

  return analysis;
}

function getFallbackResources(context) {
  const resourceMap = {
    mathematics: [
      {
        title: 'Cambridge Primary Mathematics',
        description: 'Official Cambridge mathematics curriculum and resources',
        url: 'https://www.cambridge.org/gb/education/subject/mathematics/cambridge-primary-mathematics',
        type: 'Curriculum',
        level: 'Primary',
        subject: 'mathematics'
      },
      {
        title: 'Math is Fun',
        description: 'Interactive math lessons and practice problems',
        url: 'https://www.mathsisfun.com/',
        type: 'Practice',
        level: 'Primary',
        subject: 'mathematics'
      }
    ],
    science: [
      {
        title: 'Cambridge Primary Science',
        description: 'Official Cambridge science curriculum resources',
        url: 'https://www.cambridge.org/gb/education/subject/science/cambridge-primary-science',
        type: 'Curriculum',
        level: 'Primary',
        subject: 'science'
      },
      {
        title: 'BBC Bitesize Science',
        description: 'Interactive science lessons and experiments',
        url: 'https://www.bbc.co.uk/bitesize/subjects/z2pfb9q',
        type: 'Interactive',
        level: 'Primary',
        subject: 'science'
      }
    ],
    esl: [
      {
        title: 'Cambridge English for Young Learners',
        description: 'ESL resources and practice materials',
        url: 'https://www.cambridgeenglish.org/learning-english/parents-and-children/',
        type: 'Language Learning',
        level: 'Primary',
        subject: 'esl'
      },
      {
        title: 'British Council LearnEnglish Kids',
        description: 'Games, stories, and activities for young English learners',
        url: 'https://learnenglishkids.britishcouncil.org/',
        type: 'Interactive',
        level: 'Primary',
        subject: 'esl'
      }
    ]
  };

  const subjectResources = resourceMap[context?.subject] || [];
  const generalResources = [
    {
      title: 'BBC Bitesize Primary',
      description: 'Comprehensive primary education resources',
      url: 'https://www.bbc.co.uk/bitesize/primary',
      type: 'Multi-subject',
      level: 'Primary',
      subject: 'general'
    }
  ];

  return {
    resources: [...subjectResources, ...generalResources].slice(0, 6)
  };
}

// Run all demos
function runAllDemos() {
  console.log('🎓 Cambridge AI Tutor Extension - New Features Demo\n');
  
  demoContentAnalysis();
  demoBookmarkSystem();
  demoRelatedResources();
  demoTabSystem();
  
  console.log('✅ All demos completed successfully!');
  console.log('\nNew features implemented:');
  console.log('• Enhanced webpage content analysis for educational context detection');
  console.log('• Floating help widget with AI tutor access and tabbed interface');
  console.log('• Bookmark system for educational resources with subject categorization');
  console.log('• Related resources system with fallback content');
  console.log('• Cross-platform synchronization support');
  console.log('• Comprehensive integration tests');
}

// Export for testing or run directly
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    performLocalAnalysis,
    getFallbackResources,
    demoContentAnalysis,
    demoBookmarkSystem,
    demoRelatedResources,
    demoTabSystem,
    runAllDemos
  };
} else {
  // Run demos if script is executed directly
  runAllDemos();
}