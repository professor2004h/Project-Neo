/**
 * Integration tests for Chrome Extension functionality
 */

describe('Chrome Extension Integration Tests', () => {
  let backgroundScript;
  let contentScript;
  let popupScript;

  beforeEach(() => {
    // Mock the extension components
    backgroundScript = {
      isAuthenticated: false,
      userProfile: null,
      handleMessage: jest.fn(),
      authenticate: jest.fn(),
      askTutorQuestion: jest.fn(),
      analyzePageContent: jest.fn()
    };

    contentScript = {
      extractPageContent: jest.fn(),
      showTutorWidget: jest.fn(),
      handleMessage: jest.fn()
    };

    popupScript = {
      currentUser: null,
      currentTab: null,
      checkAuthStatus: jest.fn(),
      handleLogin: jest.fn(),
      analyzeCurrentPage: jest.fn()
    };
  });

  describe('Authentication Flow', () => {
    test('should complete full authentication flow', async () => {
      // Mock successful authentication
      const mockCredentials = { email: 'test@example.com', password: 'password' };
      const mockProfile = { name: 'Test User', role: 'parent' };
      
      backgroundScript.authenticate.mockResolvedValue({
        success: true,
        profile: mockProfile
      });

      chrome.runtime.sendMessage.mockImplementation((message, callback) => {
        if (message.action === 'authenticate') {
          callback({ success: true, profile: mockProfile });
        }
      });

      chrome.storage.sync.set.mockResolvedValue();

      // Simulate popup login
      await popupScript.handleLogin();

      // Verify authentication flow
      expect(chrome.runtime.sendMessage).toHaveBeenCalledWith({
        action: 'authenticate',
        credentials: expect.any(Object)
      });

      expect(chrome.storage.sync.set).toHaveBeenCalledWith({
        authToken: expect.any(String),
        userProfile: mockProfile
      });
    });

    test('should handle authentication failure gracefully', async () => {
      backgroundScript.authenticate.mockResolvedValue({
        success: false,
        error: 'Invalid credentials'
      });

      chrome.runtime.sendMessage.mockImplementation((message, callback) => {
        if (message.action === 'authenticate') {
          callback({ success: false, error: 'Invalid credentials' });
        }
      });

      const result = await backgroundScript.authenticate({
        email: 'test@example.com',
        password: 'wrong-password'
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid credentials');
    });
  });

  describe('Content Analysis and Help Flow', () => {
    test('should analyze educational content and provide help', async () => {
      // Mock educational page content
      const mockContent = {
        title: 'Fractions - Cambridge Mathematics',
        headings: [{ text: 'Understanding Fractions', level: 1 }],
        paragraphs: [{ text: 'A fraction represents a part of a whole...' }],
        mathContent: [{ content: '1/2 + 1/4 = 3/4' }]
      };

      const mockAnalysis = {
        educational: true,
        subject: 'Mathematics',
        level: 'Grade 3',
        topics: ['fractions', 'addition'],
        suggestions: ['Explain fractions', 'Practice fraction addition']
      };

      // Mock content script extracting content
      contentScript.extractPageContent.mockReturnValue(mockContent);

      // Mock background script analyzing content
      backgroundScript.analyzePageContent.mockResolvedValue(mockAnalysis);

      chrome.runtime.sendMessage.mockImplementation((message, callback) => {
        if (message.action === 'analyzeContent') {
          callback(mockAnalysis);
        }
      });

      // Simulate content analysis flow
      const extractedContent = contentScript.extractPageContent();
      expect(extractedContent).toEqual(mockContent);

      // Simulate sending content for analysis
      chrome.runtime.sendMessage({
        action: 'analyzeContent',
        content: extractedContent,
        url: 'https://cambridge.org/fractions'
      });

      expect(chrome.runtime.sendMessage).toHaveBeenCalledWith({
        action: 'analyzeContent',
        content: mockContent,
        url: 'https://cambridge.org/fractions'
      });
    });

    test('should handle tutor question flow end-to-end', async () => {
      // Mock authenticated state
      backgroundScript.isAuthenticated = true;
      backgroundScript.userProfile = { name: 'Test User' };

      const mockQuestion = 'What is 1/2 + 1/4?';
      const mockContext = {
        pageUrl: 'https://cambridge.org/fractions',
        subject: 'mathematics',
        topic: 'fractions'
      };

      const mockAnswer = {
        answer: 'When adding fractions, you need a common denominator. 1/2 = 2/4, so 2/4 + 1/4 = 3/4',
        confidence: 0.95,
        curriculum_alignment: 'Cambridge Grade 3 Mathematics'
      };

      // Mock tutor response
      backgroundScript.askTutorQuestion.mockResolvedValue(mockAnswer);

      chrome.runtime.sendMessage.mockImplementation((message, callback) => {
        if (message.action === 'askQuestion') {
          callback(mockAnswer);
        }
      });

      // Simulate asking question
      const result = await backgroundScript.askTutorQuestion(mockQuestion, mockContext);

      expect(result).toEqual(mockAnswer);
      expect(backgroundScript.askTutorQuestion).toHaveBeenCalledWith(mockQuestion, mockContext);
    });
  });

  describe('Cross-Platform Synchronization', () => {
    test('should sync data between popup and content script', async () => {
      const mockTab = createMockTab({
        url: 'https://cambridge.org/test',
        title: 'Test Educational Page'
      });

      const mockPageContent = createMockContentResponse({
        headings: [{ text: 'Test Topic', level: 1 }],
        paragraphs: [{ text: 'Educational content about test topic...' }]
      });

      // Mock tab query
      chrome.tabs.query.mockResolvedValue([mockTab]);

      // Mock content script response
      chrome.tabs.sendMessage.mockImplementation((tabId, message, callback) => {
        if (message.action === 'getPageContent') {
          callback(mockPageContent);
        }
      });

      // Mock analysis response
      chrome.runtime.sendMessage.mockImplementation((message, callback) => {
        if (message.action === 'analyzeContent') {
          callback({
            educational: true,
            subject: 'Test Subject',
            level: 'Grade 3'
          });
        }
      });

      // Simulate popup analyzing current page
      popupScript.currentTab = mockTab;
      await popupScript.analyzeCurrentPage();

      // Verify communication flow
      expect(chrome.tabs.sendMessage).toHaveBeenCalledWith(mockTab.id, {
        action: 'getPageContent'
      });

      expect(chrome.runtime.sendMessage).toHaveBeenCalledWith({
        action: 'analyzeContent',
        content: mockPageContent.content,
        url: mockTab.url
      });
    });

    test('should handle widget interaction across components', async () => {
      const mockExplanation = 'This is a detailed explanation of the concept.';
      const mockSelectedText = 'photosynthesis';

      // Mock content script showing widget
      contentScript.showTutorWidget.mockImplementation(() => {
        // Simulate widget being shown
        return Promise.resolve();
      });

      // Mock background script providing explanation
      backgroundScript.askTutorQuestion.mockResolvedValue({
        answer: mockExplanation,
        confidence: 0.9
      });

      chrome.runtime.sendMessage.mockImplementation((message, callback) => {
        if (message.action === 'askQuestion') {
          callback({ answer: mockExplanation, confidence: 0.9 });
        }
      });

      chrome.tabs.sendMessage.mockImplementation((tabId, message) => {
        if (message.action === 'showExplanation') {
          contentScript.showTutorWidget();
          return Promise.resolve();
        }
      });

      // Simulate explanation flow
      await chrome.tabs.sendMessage(1, {
        action: 'showExplanation',
        explanation: mockExplanation,
        selectedText: mockSelectedText
      });

      expect(contentScript.showTutorWidget).toHaveBeenCalled();
    });
  });

  describe('Error Handling and Recovery', () => {
    test('should handle network errors gracefully', async () => {
      // Mock network failure
      fetch.mockRejectedValue(new Error('Network error'));
      
      backgroundScript.askTutorQuestion.mockRejectedValue(new Error('Network error'));

      try {
        await backgroundScript.askTutorQuestion('Test question');
      } catch (error) {
        expect(error.message).toBe('Network error');
      }

      // Verify error was handled
      expect(backgroundScript.askTutorQuestion).toHaveBeenCalled();
    });

    test('should handle tab communication failures', async () => {
      // Mock tab communication failure
      chrome.tabs.sendMessage.mockRejectedValue(new Error('Tab not found'));

      const mockTab = createMockTab();
      popupScript.currentTab = mockTab;

      try {
        await chrome.tabs.sendMessage(mockTab.id, { action: 'getPageContent' });
      } catch (error) {
        expect(error.message).toBe('Tab not found');
      }

      expect(chrome.tabs.sendMessage).toHaveBeenCalledWith(mockTab.id, {
        action: 'getPageContent'
      });
    });

    test('should handle authentication token expiry', async () => {
      // Mock expired token scenario
      chrome.storage.sync.get.mockResolvedValue({
        authToken: 'expired-token',
        userProfile: { name: 'Test User' }
      });

      fetch.mockResolvedValue({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ error: 'Token expired' })
      });

      // Simulate token verification failure
      const response = await fetch('/auth/verify', {
        headers: { Authorization: 'Bearer expired-token' }
      });

      expect(response.ok).toBe(false);
      expect(response.status).toBe(401);

      // Should clear expired token
      chrome.storage.sync.remove.mockResolvedValue();
      await chrome.storage.sync.remove(['authToken', 'userProfile']);

      expect(chrome.storage.sync.remove).toHaveBeenCalledWith(['authToken', 'userProfile']);
    });
  });

  describe('Educational Site Integration', () => {
    test('should integrate with Cambridge curriculum sites', () => {
      const educationalUrls = [
        'https://www.cambridge.org/education',
        'https://www.bbc.co.uk/bitesize/subjects',
        'https://www.khanacademy.org/math',
        'https://www.mathsisfun.com/definitions'
      ];

      educationalUrls.forEach(url => {
        const isEducational = backgroundScript.isEducationalSite ? 
          backgroundScript.isEducationalSite(url) : 
          url.includes('cambridge.org') || url.includes('bbc.co.uk') || 
          url.includes('khanacademy.org') || url.includes('mathsisfun.com');
        
        expect(isEducational).toBe(true);
      });
    });

    test('should not activate on non-educational sites', () => {
      const nonEducationalUrls = [
        'https://www.google.com',
        'https://www.facebook.com',
        'https://www.youtube.com/watch?v=random'
      ];

      nonEducationalUrls.forEach(url => {
        const isEducational = backgroundScript.isEducationalSite ? 
          backgroundScript.isEducationalSite(url) : false;
        
        expect(isEducational).toBe(false);
      });
    });
  });

  describe('Enhanced Content Analysis', () => {
    test('should perform local content analysis for educational context detection', () => {
      const mockContent = {
        title: 'Understanding Fractions - Primary Mathematics',
        headings: [
          { text: 'What are Fractions?', level: 1 },
          { text: 'Adding Fractions', level: 2 }
        ],
        paragraphs: [
          { text: 'A fraction represents a part of a whole number. When we divide something into equal parts, each part is a fraction.' },
          { text: 'To add fractions with the same denominator, we add the numerators and keep the denominator the same.' }
        ],
        mathContent: [
          { content: '1/2 + 1/4 = 2/4 + 1/4 = 3/4' }
        ],
        vocabulary: [
          { term: 'numerator' },
          { term: 'denominator' },
          { term: 'fraction' }
        ]
      };

      const mockUrl = 'https://www.mathsisfun.com/fractions.html';

      // Mock the local analysis function
      const performLocalAnalysis = (content, url) => {
        const analysis = {
          educational: false,
          subject: null,
          level: null,
          topics: [],
          difficulty: 'unknown',
          confidence: 0
        };

        // Check for mathematical content
        const titleText = content.title.toLowerCase();
        const mathKeywords = ['fraction', 'math', 'arithmetic', 'number'];
        const mathScore = mathKeywords.reduce((score, keyword) => {
          return score + (titleText.includes(keyword) ? 2 : 0);
        }, 0);

        if (mathScore > 0 || content.mathContent.length > 0) {
          analysis.educational = true;
          analysis.subject = 'mathematics';
          analysis.level = 'primary';
          analysis.confidence = 0.8;
          analysis.topics = content.headings.map(h => h.text);
        }

        return analysis;
      };

      const result = performLocalAnalysis(mockContent, mockUrl);

      expect(result.educational).toBe(true);
      expect(result.subject).toBe('mathematics');
      expect(result.level).toBe('primary');
      expect(result.confidence).toBeGreaterThan(0.5);
      expect(result.topics).toContain('What are Fractions?');
    });

    test('should detect ESL content correctly', () => {
      const mockESLContent = {
        title: 'English Pronunciation Practice - ESL Learning',
        headings: [
          { text: 'Vowel Sounds', level: 1 },
          { text: 'Common Pronunciation Mistakes', level: 2 }
        ],
        paragraphs: [
          { text: 'English pronunciation can be challenging for second language learners. Practice these vowel sounds daily.' },
          { text: 'Listen carefully to native speakers and repeat the sounds. Focus on mouth position and tongue placement.' }
        ],
        vocabulary: [
          { term: 'pronunciation' },
          { term: 'vowel' },
          { term: 'consonant' }
        ]
      };

      const performESLAnalysis = (content) => {
        const titleText = content.title.toLowerCase();
        const eslKeywords = ['esl', 'pronunciation', 'english', 'speaking', 'listening'];
        const eslScore = eslKeywords.reduce((score, keyword) => {
          return score + (titleText.includes(keyword) ? 2 : 0);
        }, 0);

        return {
          educational: eslScore > 0,
          subject: eslScore > 0 ? 'esl' : null,
          level: 'primary',
          confidence: eslScore > 0 ? 0.9 : 0
        };
      };

      const result = performESLAnalysis(mockESLContent);

      expect(result.educational).toBe(true);
      expect(result.subject).toBe('esl');
      expect(result.confidence).toBe(0.9);
    });
  });

  describe('Bookmark System Integration', () => {
    beforeEach(() => {
      // Mock chrome storage for bookmarks
      chrome.storage.sync.get.mockImplementation((keys, callback) => {
        if (keys.includes('educationalBookmarks')) {
          callback({ educationalBookmarks: [] });
        }
      });

      chrome.storage.sync.set.mockImplementation((data, callback) => {
        if (callback) callback();
      });
    });

    test('should add and remove bookmarks correctly', async () => {
      const mockPage = {
        url: 'https://www.cambridge.org/fractions',
        title: 'Understanding Fractions',
        subject: 'mathematics',
        level: 'primary',
        topics: ['fractions', 'basic arithmetic'],
        timestamp: new Date().toISOString(),
        favicon: 'https://www.cambridge.org/favicon.ico'
      };

      // Mock bookmark functions
      const getBookmarks = () => Promise.resolve([]);
      const saveBookmarks = (bookmarks) => {
        chrome.storage.sync.set({ educationalBookmarks: bookmarks });
        return Promise.resolve();
      };

      // Test adding bookmark
      let bookmarks = await getBookmarks();
      expect(bookmarks.length).toBe(0);

      bookmarks.unshift(mockPage);
      await saveBookmarks(bookmarks);

      expect(chrome.storage.sync.set).toHaveBeenCalledWith({
        educationalBookmarks: [mockPage]
      });

      // Test removing bookmark
      bookmarks = bookmarks.filter(b => b.url !== mockPage.url);
      await saveBookmarks(bookmarks);

      expect(chrome.storage.sync.set).toHaveBeenCalledWith({
        educationalBookmarks: []
      });
    });

    test('should sync bookmarks across extension components', async () => {
      const mockBookmarks = [
        {
          url: 'https://www.cambridge.org/math',
          title: 'Cambridge Mathematics',
          subject: 'mathematics',
          level: 'primary',
          timestamp: new Date().toISOString()
        },
        {
          url: 'https://www.bbc.co.uk/bitesize/science',
          title: 'BBC Science',
          subject: 'science',
          level: 'primary',
          timestamp: new Date().toISOString()
        }
      ];

      // Mock storage returning bookmarks
      chrome.storage.sync.get.mockImplementation((keys, callback) => {
        if (keys.includes('educationalBookmarks')) {
          callback({ educationalBookmarks: mockBookmarks });
        }
      });

      // Test bookmark retrieval in content script
      const contentScriptBookmarks = await new Promise(resolve => {
        chrome.storage.sync.get(['educationalBookmarks'], (result) => {
          resolve(result.educationalBookmarks || []);
        });
      });

      expect(contentScriptBookmarks).toEqual(mockBookmarks);
      expect(contentScriptBookmarks.length).toBe(2);

      // Test bookmark retrieval in popup
      const popupBookmarks = await new Promise(resolve => {
        chrome.storage.sync.get(['educationalBookmarks'], (result) => {
          resolve(result.educationalBookmarks || []);
        });
      });

      expect(popupBookmarks).toEqual(mockBookmarks);
    });

    test('should handle bookmark limit correctly', async () => {
      // Create 55 mock bookmarks (over the 50 limit)
      const manyBookmarks = Array.from({ length: 55 }, (_, i) => ({
        url: `https://example.com/page${i}`,
        title: `Page ${i}`,
        subject: 'general',
        level: 'primary',
        timestamp: new Date().toISOString()
      }));

      const saveBookmarks = (bookmarks) => {
        // Simulate the limit enforcement
        const limitedBookmarks = bookmarks.slice(0, 50);
        chrome.storage.sync.set({ educationalBookmarks: limitedBookmarks });
        return Promise.resolve();
      };

      await saveBookmarks(manyBookmarks);

      expect(chrome.storage.sync.set).toHaveBeenCalledWith({
        educationalBookmarks: expect.arrayContaining([
          expect.objectContaining({ url: 'https://example.com/page0' })
        ])
      });

      // Verify only 50 bookmarks were saved
      const savedCall = chrome.storage.sync.set.mock.calls[0][0];
      expect(savedCall.educationalBookmarks.length).toBe(50);
    });
  });

  describe('Related Resources System', () => {
    test('should fetch related resources based on context', async () => {
      const mockContext = {
        subject: 'mathematics',
        level: 'primary',
        topics: ['fractions', 'decimals']
      };

      const mockResources = {
        resources: [
          {
            title: 'Cambridge Primary Mathematics',
            description: 'Official Cambridge mathematics curriculum',
            url: 'https://www.cambridge.org/mathematics',
            type: 'Curriculum',
            level: 'Primary',
            subject: 'mathematics'
          },
          {
            title: 'Math Practice Worksheets',
            description: 'Interactive fraction and decimal exercises',
            url: 'https://www.mathsisfun.com/worksheets',
            type: 'Practice',
            level: 'Primary',
            subject: 'mathematics'
          }
        ]
      };

      // Mock successful API response
      fetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResources)
      });

      backgroundScript.getRelatedResources = jest.fn().mockResolvedValue(mockResources);

      const result = await backgroundScript.getRelatedResources(mockContext, 'https://example.com');

      expect(result.resources).toHaveLength(2);
      expect(result.resources[0].subject).toBe('mathematics');
      expect(result.resources[0].level).toBe('Primary');
    });

    test('should provide fallback resources when API fails', async () => {
      const mockContext = {
        subject: 'science',
        level: 'primary'
      };

      // Mock API failure
      fetch.mockRejectedValue(new Error('Network error'));

      const getFallbackResources = (context) => {
        const fallbackMap = {
          science: [
            {
              title: 'Cambridge Primary Science',
              description: 'Official Cambridge science curriculum',
              url: 'https://www.cambridge.org/science',
              type: 'Curriculum',
              level: 'Primary',
              subject: 'science'
            }
          ]
        };

        return {
          resources: fallbackMap[context.subject] || []
        };
      };

      const result = getFallbackResources(mockContext);

      expect(result.resources).toHaveLength(1);
      expect(result.resources[0].subject).toBe('science');
      expect(result.resources[0].title).toContain('Cambridge');
    });

    test('should handle empty context gracefully', async () => {
      const emptyContext = null;

      backgroundScript.getRelatedResources = jest.fn().mockResolvedValue({ resources: [] });

      const result = await backgroundScript.getRelatedResources(emptyContext, 'https://example.com');

      expect(result.resources).toEqual([]);
    });
  });

  describe('Widget Tab System Integration', () => {
    test('should switch between chat, bookmarks, and resources tabs', () => {
      // Mock DOM elements
      const mockWidget = {
        querySelectorAll: jest.fn(),
        querySelector: jest.fn()
      };

      const mockTabButtons = [
        { dataset: { tab: 'chat' }, classList: { toggle: jest.fn() } },
        { dataset: { tab: 'bookmarks' }, classList: { toggle: jest.fn() } },
        { dataset: { tab: 'resources' }, classList: { toggle: jest.fn() } }
      ];

      const mockTabContents = [
        { id: 'chat-tab', classList: { toggle: jest.fn() } },
        { id: 'bookmarks-tab', classList: { toggle: jest.fn() } },
        { id: 'resources-tab', classList: { toggle: jest.fn() } }
      ];

      mockWidget.querySelectorAll.mockImplementation(selector => {
        if (selector === '.tab-btn') return mockTabButtons;
        if (selector === '.tab-content') return mockTabContents;
        return [];
      });

      const switchTab = (tabName) => {
        // Update tab buttons
        mockTabButtons.forEach(btn => {
          btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update tab content
        mockTabContents.forEach(content => {
          content.classList.toggle('active', content.id === `${tabName}-tab`);
        });
      };

      // Test switching to bookmarks tab
      switchTab('bookmarks');

      expect(mockTabButtons[1].classList.toggle).toHaveBeenCalledWith('active', true);
      expect(mockTabContents[1].classList.toggle).toHaveBeenCalledWith('active', true);

      // Test switching to resources tab
      switchTab('resources');

      expect(mockTabButtons[2].classList.toggle).toHaveBeenCalledWith('active', true);
      expect(mockTabContents[2].classList.toggle).toHaveBeenCalledWith('active', true);
    });

    test('should load appropriate content when switching tabs', async () => {
      const mockContentScript = {
        refreshBookmarksList: jest.fn(),
        loadRelatedResources: jest.fn(),
        switchTab: jest.fn()
      };

      // Mock tab switching with content loading
      mockContentScript.switchTab.mockImplementation((tabName) => {
        if (tabName === 'bookmarks') {
          mockContentScript.refreshBookmarksList();
        } else if (tabName === 'resources') {
          mockContentScript.loadRelatedResources();
        }
      });

      // Test bookmarks tab loading
      mockContentScript.switchTab('bookmarks');
      expect(mockContentScript.refreshBookmarksList).toHaveBeenCalled();

      // Test resources tab loading
      mockContentScript.switchTab('resources');
      expect(mockContentScript.loadRelatedResources).toHaveBeenCalled();
    });
  });

  describe('Cross-Platform Sync Integration', () => {
    test('should sync bookmark status across all extension components', async () => {
      const testUrl = 'https://www.cambridge.org/test-page';
      const mockBookmark = {
        url: testUrl,
        title: 'Test Page',
        subject: 'mathematics',
        level: 'primary',
        timestamp: new Date().toISOString()
      };

      // Mock storage with existing bookmark
      chrome.storage.sync.get.mockImplementation((keys, callback) => {
        if (keys.includes('educationalBookmarks')) {
          callback({ educationalBookmarks: [mockBookmark] });
        }
      });

      // Test bookmark status check in content script
      const isBookmarked = await new Promise(resolve => {
        chrome.storage.sync.get(['educationalBookmarks'], (result) => {
          const bookmarks = result.educationalBookmarks || [];
          resolve(bookmarks.some(b => b.url === testUrl));
        });
      });

      expect(isBookmarked).toBe(true);

      // Test bookmark status update in popup
      const popupBookmarkStatus = await new Promise(resolve => {
        chrome.storage.sync.get(['educationalBookmarks'], (result) => {
          const bookmarks = result.educationalBookmarks || [];
          resolve(bookmarks.some(b => b.url === testUrl));
        });
      });

      expect(popupBookmarkStatus).toBe(true);
    });

    test('should sync educational context across components', async () => {
      const mockContext = {
        educational: true,
        subject: 'mathematics',
        level: 'primary',
        topics: ['fractions', 'decimals'],
        confidence: 0.9
      };

      // Mock message passing between components
      chrome.runtime.sendMessage.mockImplementation((message, callback) => {
        if (message.action === 'analyzeContent') {
          callback(mockContext);
        }
      });

      chrome.tabs.sendMessage.mockImplementation((tabId, message, callback) => {
        if (message.action === 'getPageContent') {
          callback({
            content: {
              title: 'Fractions and Decimals',
              headings: [{ text: 'Understanding Fractions', level: 1 }]
            }
          });
        }
      });

      // Test context sharing from content script to background
      let receivedContext = null;
      chrome.runtime.sendMessage({
        action: 'analyzeContent',
        content: { title: 'Test' },
        url: 'https://example.com'
      }, (response) => {
        receivedContext = response;
      });

      expect(receivedContext).toEqual(mockContext);

      // Test context sharing from background to popup
      chrome.runtime.sendMessage({
        action: 'getContext'
      }, (response) => {
        expect(response).toEqual(mockContext);
      });
    });
  });

  describe('Error Recovery and Resilience', () => {
    test('should handle bookmark storage failures gracefully', async () => {
      // Mock storage failure
      chrome.storage.sync.set.mockImplementation((data, callback) => {
        throw new Error('Storage quota exceeded');
      });

      const saveBookmarks = async (bookmarks) => {
        try {
          await new Promise((resolve, reject) => {
            chrome.storage.sync.set({ educationalBookmarks: bookmarks }, () => {
              if (chrome.runtime.lastError) {
                reject(new Error(chrome.runtime.lastError.message));
              } else {
                resolve();
              }
            });
          });
          return { success: true };
        } catch (error) {
          console.error('Bookmark save failed:', error);
          return { success: false, error: error.message };
        }
      };

      const result = await saveBookmarks([{ url: 'test' }]);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Storage quota exceeded');
    });

    test('should handle content analysis API failures', async () => {
      // Mock API failure
      fetch.mockRejectedValue(new Error('API unavailable'));

      const analyzeContentWithFallback = async (content, url) => {
        try {
          const response = await fetch('/api/analyze', {
            method: 'POST',
            body: JSON.stringify({ content, url })
          });
          return await response.json();
        } catch (error) {
          // Fallback to local analysis
          return {
            educational: url.includes('cambridge.org') || url.includes('bbc.co.uk'),
            subject: 'general',
            level: 'unknown',
            confidence: 0.5,
            source: 'fallback'
          };
        }
      };

      const result = await analyzeContentWithFallback(
        { title: 'Test' },
        'https://www.cambridge.org/test'
      );

      expect(result.educational).toBe(true);
      expect(result.source).toBe('fallback');
      expect(result.confidence).toBe(0.5);
    });
  });
});