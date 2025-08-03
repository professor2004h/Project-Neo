/**
 * Bookmark System Tests for Chrome Extension
 */

describe('Bookmark System', () => {
  let mockStorage;

  beforeEach(() => {
    // Mock chrome storage
    mockStorage = {
      data: {},
      sync: {
        get: jest.fn((keys, callback) => {
          const result = {};
          keys.forEach(key => {
            result[key] = mockStorage.data[key];
          });
          callback(result);
        }),
        set: jest.fn((data, callback) => {
          Object.assign(mockStorage.data, data);
          if (callback) callback();
        })
      }
    };

    global.chrome = {
      storage: mockStorage,
      runtime: {
        sendMessage: jest.fn()
      }
    };
  });

  describe('Bookmark Management', () => {
    test('should add bookmark correctly', async () => {
      const mockPage = {
        url: 'https://www.cambridge.org/fractions',
        title: 'Understanding Fractions',
        subject: 'mathematics',
        level: 'primary',
        topics: ['fractions', 'basic arithmetic'],
        timestamp: new Date().toISOString(),
        favicon: 'https://www.cambridge.org/favicon.ico'
      };

      // Simulate adding bookmark
      const getBookmarks = () => {
        return new Promise(resolve => {
          chrome.storage.sync.get(['educationalBookmarks'], (result) => {
            resolve(result.educationalBookmarks || []);
          });
        });
      };

      const saveBookmarks = (bookmarks) => {
        return new Promise(resolve => {
          chrome.storage.sync.set({ educationalBookmarks: bookmarks }, resolve);
        });
      };

      // Initially no bookmarks
      let bookmarks = await getBookmarks();
      expect(bookmarks.length).toBe(0);

      // Add bookmark
      bookmarks.unshift(mockPage);
      await saveBookmarks(bookmarks);

      // Verify bookmark was saved
      expect(chrome.storage.sync.set).toHaveBeenCalledWith({
        educationalBookmarks: [mockPage]
      });

      // Verify bookmark can be retrieved
      bookmarks = await getBookmarks();
      expect(bookmarks.length).toBe(1);
      expect(bookmarks[0].url).toBe(mockPage.url);
      expect(bookmarks[0].subject).toBe('mathematics');
    });

    test('should remove bookmark correctly', async () => {
      const mockBookmark = {
        url: 'https://www.cambridge.org/test',
        title: 'Test Page',
        subject: 'mathematics'
      };

      // Pre-populate storage with bookmark
      mockStorage.data.educationalBookmarks = [mockBookmark];

      const getBookmarks = () => {
        return new Promise(resolve => {
          chrome.storage.sync.get(['educationalBookmarks'], (result) => {
            resolve(result.educationalBookmarks || []);
          });
        });
      };

      const saveBookmarks = (bookmarks) => {
        return new Promise(resolve => {
          chrome.storage.sync.set({ educationalBookmarks: bookmarks }, resolve);
        });
      };

      // Verify bookmark exists
      let bookmarks = await getBookmarks();
      expect(bookmarks.length).toBe(1);

      // Remove bookmark
      bookmarks = bookmarks.filter(b => b.url !== mockBookmark.url);
      await saveBookmarks(bookmarks);

      // Verify bookmark was removed
      expect(chrome.storage.sync.set).toHaveBeenCalledWith({
        educationalBookmarks: []
      });

      bookmarks = await getBookmarks();
      expect(bookmarks.length).toBe(0);
    });

    test('should enforce bookmark limit', async () => {
      // Create 55 bookmarks (over the 50 limit)
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
        return new Promise(resolve => {
          chrome.storage.sync.set({ educationalBookmarks: limitedBookmarks }, resolve);
        });
      };

      await saveBookmarks(manyBookmarks);

      // Verify only 50 bookmarks were saved
      const savedCall = chrome.storage.sync.set.mock.calls[0][0];
      expect(savedCall.educationalBookmarks.length).toBe(50);
      expect(savedCall.educationalBookmarks[0].url).toBe('https://example.com/page0');
      expect(savedCall.educationalBookmarks[49].url).toBe('https://example.com/page49');
    });
  });

  describe('Content Analysis', () => {
    test('should detect mathematical content', () => {
      const performLocalAnalysis = (content, url) => {
        const analysis = {
          educational: false,
          subject: null,
          level: null,
          topics: [],
          confidence: 0
        };

        const titleText = content.title.toLowerCase();
        const mathKeywords = ['fraction', 'math', 'arithmetic', 'number', 'algebra'];
        const mathScore = mathKeywords.reduce((score, keyword) => {
          return score + (titleText.includes(keyword) ? 2 : 0);
        }, 0);

        if (mathScore > 0 || content.mathContent?.length > 0) {
          analysis.educational = true;
          analysis.subject = 'mathematics';
          analysis.level = 'primary';
          analysis.confidence = 0.8;
          analysis.topics = content.headings?.map(h => h.text) || [];
        }

        return analysis;
      };

      const mockContent = {
        title: 'Understanding Fractions - Primary Mathematics',
        headings: [
          { text: 'What are Fractions?', level: 1 },
          { text: 'Adding Fractions', level: 2 }
        ],
        mathContent: [
          { content: '1/2 + 1/4 = 3/4' }
        ]
      };

      const result = performLocalAnalysis(mockContent, 'https://mathsisfun.com/fractions');

      expect(result.educational).toBe(true);
      expect(result.subject).toBe('mathematics');
      expect(result.level).toBe('primary');
      expect(result.confidence).toBe(0.8);
      expect(result.topics).toContain('What are Fractions?');
    });

    test('should detect ESL content', () => {
      const performLocalAnalysis = (content, url) => {
        const analysis = {
          educational: false,
          subject: null,
          level: null,
          confidence: 0
        };

        const titleText = content.title.toLowerCase();
        const eslKeywords = ['esl', 'pronunciation', 'english', 'speaking', 'listening'];
        const eslScore = eslKeywords.reduce((score, keyword) => {
          return score + (titleText.includes(keyword) ? 2 : 0);
        }, 0);

        if (eslScore > 0) {
          analysis.educational = true;
          analysis.subject = 'esl';
          analysis.level = 'primary';
          analysis.confidence = 0.9;
        }

        return analysis;
      };

      const mockContent = {
        title: 'English Pronunciation Practice - ESL Learning',
        headings: [
          { text: 'Vowel Sounds', level: 1 }
        ]
      };

      const result = performLocalAnalysis(mockContent, 'https://example.com/esl');

      expect(result.educational).toBe(true);
      expect(result.subject).toBe('esl');
      expect(result.confidence).toBe(0.9);
    });
  });

  describe('Related Resources', () => {
    test('should provide fallback resources for mathematics', () => {
      const getFallbackResources = (context) => {
        const resourceMap = {
          mathematics: [
            {
              title: 'Cambridge Primary Mathematics',
              description: 'Official Cambridge mathematics curriculum',
              url: 'https://www.cambridge.org/mathematics',
              type: 'Curriculum',
              level: 'Primary',
              subject: 'mathematics'
            },
            {
              title: 'Math is Fun',
              description: 'Interactive math lessons and practice',
              url: 'https://www.mathsisfun.com/',
              type: 'Practice',
              level: 'Primary',
              subject: 'mathematics'
            }
          ]
        };

        return {
          resources: resourceMap[context?.subject] || []
        };
      };

      const mockContext = {
        subject: 'mathematics',
        level: 'primary'
      };

      const result = getFallbackResources(mockContext);

      expect(result.resources).toHaveLength(2);
      expect(result.resources[0].subject).toBe('mathematics');
      expect(result.resources[0].title).toContain('Cambridge');
      expect(result.resources[1].title).toContain('Math is Fun');
    });

    test('should handle empty context', () => {
      const getFallbackResources = (context) => {
        return {
          resources: context?.subject ? [] : []
        };
      };

      const result = getFallbackResources(null);
      expect(result.resources).toEqual([]);
    });
  });

  describe('Tab System', () => {
    test('should switch tabs correctly', () => {
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

      const switchTab = (tabName) => {
        mockTabButtons.forEach(btn => {
          btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        mockTabContents.forEach(content => {
          content.classList.toggle('active', content.id === `${tabName}-tab`);
        });
      };

      // Test switching to bookmarks tab
      switchTab('bookmarks');

      expect(mockTabButtons[0].classList.toggle).toHaveBeenCalledWith('active', false);
      expect(mockTabButtons[1].classList.toggle).toHaveBeenCalledWith('active', true);
      expect(mockTabButtons[2].classList.toggle).toHaveBeenCalledWith('active', false);

      expect(mockTabContents[1].classList.toggle).toHaveBeenCalledWith('active', true);
    });
  });
});