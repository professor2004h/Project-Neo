/**
 * Cambridge AI Tutor Chrome Extension - Background Script
 * Handles extension lifecycle, context menu, and communication between components
 */

class ExtensionBackground {
  constructor() {
    this.apiBaseUrl = 'http://localhost:8000'; // Development URL
    this.isAuthenticated = false;
    this.userProfile = null;
    this.init();
  }

  init() {
    // Set up event listeners
    chrome.runtime.onInstalled.addListener(this.handleInstalled.bind(this));
    chrome.runtime.onMessage.addListener(this.handleMessage.bind(this));
    chrome.tabs.onActivated.addListener(this.handleTabActivated.bind(this));
    chrome.tabs.onUpdated.addListener(this.handleTabUpdated.bind(this));
    
    // Initialize context menu
    this.setupContextMenu();
    
    // Check authentication status
    this.checkAuthStatus();
  }

  handleInstalled(details) {
    console.log('Cambridge AI Tutor extension installed:', details.reason);
    
    // Set default settings
    chrome.storage.sync.set({
      settings: {
        autoHelp: true,
        contextualHints: true,
        voiceEnabled: false,
        difficultyLevel: 'auto'
      }
    });

    // Show welcome notification
    if (details.reason === 'install') {
      chrome.tabs.create({
        url: chrome.runtime.getURL('welcome.html')
      });
    }
  }

  async handleMessage(request, sender, sendResponse) {
    try {
      switch (request.action) {
        case 'getAuthStatus':
          sendResponse({ authenticated: this.isAuthenticated, profile: this.userProfile });
          break;
          
        case 'authenticate':
          const authResult = await this.authenticate(request.credentials);
          sendResponse(authResult);
          break;
          
        case 'askQuestion':
          const answer = await this.askTutorQuestion(request.question, request.context);
          sendResponse(answer);
          break;
          
        case 'analyzeContent':
          const analysis = await this.analyzePageContent(request.content, request.url);
          sendResponse(analysis);
          break;
          
        case 'trackActivity':
          await this.trackLearningActivity(request.activity);
          sendResponse({ success: true });
          break;
          
        case 'getSettings':
          const settings = await this.getSettings();
          sendResponse(settings);
          break;
          
        case 'updateSettings':
          await this.updateSettings(request.settings);
          sendResponse({ success: true });
          break;

        case 'getRelatedResources':
          const resources = await this.getRelatedResources(request.context, request.url);
          sendResponse(resources);
          break;
          
        default:
          sendResponse({ error: 'Unknown action' });
      }
    } catch (error) {
      console.error('Background script error:', error);
      sendResponse({ error: error.message });
    }
    
    return true; // Keep message channel open for async response
  }

  handleTabActivated(activeInfo) {
    // Check if the active tab contains educational content
    chrome.tabs.get(activeInfo.tabId, (tab) => {
      if (tab.url && this.isEducationalSite(tab.url)) {
        this.injectContentScript(tab.id);
      }
    });
  }

  handleTabUpdated(tabId, changeInfo, tab) {
    if (changeInfo.status === 'complete' && tab.url && this.isEducationalSite(tab.url)) {
      this.injectContentScript(tabId);
    }
  }

  setupContextMenu() {
    chrome.contextMenus.create({
      id: 'explainSelection',
      title: 'Explain with AI Tutor',
      contexts: ['selection']
    });

    chrome.contextMenus.create({
      id: 'getHelp',
      title: 'Get Help with This Page',
      contexts: ['page']
    });

    chrome.contextMenus.onClicked.addListener(this.handleContextMenu.bind(this));
  }

  async handleContextMenu(info, tab) {
    switch (info.menuItemId) {
      case 'explainSelection':
        await this.explainSelectedText(info.selectionText, tab);
        break;
      case 'getHelp':
        await this.showPageHelp(tab);
        break;
    }
  }

  isEducationalSite(url) {
    const educationalDomains = [
      'cambridge.org',
      'bbc.co.uk/bitesize',
      'khanacademy.org',
      'mathsisfun.com',
      'education.com'
    ];
    
    return educationalDomains.some(domain => url.includes(domain));
  }

  async injectContentScript(tabId) {
    try {
      await chrome.scripting.executeScript({
        target: { tabId },
        files: ['content.js']
      });
    } catch (error) {
      console.error('Failed to inject content script:', error);
    }
  }

  async checkAuthStatus() {
    try {
      const result = await chrome.storage.sync.get(['authToken', 'userProfile']);
      if (result.authToken) {
        // Verify token with backend
        const response = await fetch(`${this.apiBaseUrl}/auth/verify`, {
          headers: {
            'Authorization': `Bearer ${result.authToken}`
          }
        });
        
        if (response.ok) {
          this.isAuthenticated = true;
          this.userProfile = result.userProfile;
        } else {
          // Token expired, clear storage
          await chrome.storage.sync.remove(['authToken', 'userProfile']);
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    }
  }

  async authenticate(credentials) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(credentials)
      });

      if (response.ok) {
        const data = await response.json();
        await chrome.storage.sync.set({
          authToken: data.token,
          userProfile: data.profile
        });
        
        this.isAuthenticated = true;
        this.userProfile = data.profile;
        
        return { success: true, profile: data.profile };
      } else {
        return { success: false, error: 'Authentication failed' };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async askTutorQuestion(question, context = {}) {
    if (!this.isAuthenticated) {
      throw new Error('User not authenticated');
    }

    try {
      const authToken = await this.getAuthToken();
      const response = await fetch(`${this.apiBaseUrl}/tutor/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          question,
          context: {
            ...context,
            source: 'chrome_extension',
            timestamp: new Date().toISOString()
          }
        })
      });

      if (response.ok) {
        return await response.json();
      } else {
        throw new Error('Failed to get tutor response');
      }
    } catch (error) {
      console.error('Tutor question failed:', error);
      throw error;
    }
  }

  async analyzePageContent(content, url) {
    if (!this.isAuthenticated) {
      return { educational: false };
    }

    try {
      const authToken = await this.getAuthToken();
      const response = await fetch(`${this.apiBaseUrl}/content/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          content,
          url,
          source: 'chrome_extension'
        })
      });

      if (response.ok) {
        return await response.json();
      } else {
        return { educational: false };
      }
    } catch (error) {
      console.error('Content analysis failed:', error);
      return { educational: false };
    }
  }

  async trackLearningActivity(activity) {
    if (!this.isAuthenticated) {
      return;
    }

    try {
      const authToken = await this.getAuthToken();
      await fetch(`${this.apiBaseUrl}/progress/track`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          ...activity,
          source: 'chrome_extension',
          timestamp: new Date().toISOString()
        })
      });
    } catch (error) {
      console.error('Activity tracking failed:', error);
    }
  }

  async explainSelectedText(text, tab) {
    try {
      const context = {
        selectedText: text,
        pageUrl: tab.url,
        pageTitle: tab.title
      };
      
      const explanation = await this.askTutorQuestion(`Please explain: ${text}`, context);
      
      // Send explanation to content script
      chrome.tabs.sendMessage(tab.id, {
        action: 'showExplanation',
        explanation,
        selectedText: text
      });
    } catch (error) {
      console.error('Failed to explain selection:', error);
    }
  }

  async showPageHelp(tab) {
    try {
      // Get page content analysis
      chrome.tabs.sendMessage(tab.id, {
        action: 'getPageContent'
      }, async (response) => {
        if (response && response.content) {
          const analysis = await this.analyzePageContent(response.content, tab.url);
          
          chrome.tabs.sendMessage(tab.id, {
            action: 'showPageHelp',
            analysis
          });
        }
      });
    } catch (error) {
      console.error('Failed to show page help:', error);
    }
  }

  async getAuthToken() {
    const result = await chrome.storage.sync.get(['authToken']);
    return result.authToken;
  }

  async getSettings() {
    const result = await chrome.storage.sync.get(['settings']);
    return result.settings || {
      autoHelp: true,
      contextualHints: true,
      voiceEnabled: false,
      difficultyLevel: 'auto'
    };
  }

  async updateSettings(settings) {
    await chrome.storage.sync.set({ settings });
  }

  async getRelatedResources(context, url) {
    if (!this.isAuthenticated || !context) {
      return { resources: [] };
    }

    try {
      const authToken = await this.getAuthToken();
      const response = await fetch(`${this.apiBaseUrl}/content/related-resources`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          context,
          url,
          source: 'chrome_extension'
        })
      });

      if (response.ok) {
        return await response.json();
      } else {
        // Return fallback resources if API fails
        return this.getFallbackResources(context);
      }
    } catch (error) {
      console.error('Related resources fetch failed:', error);
      return this.getFallbackResources(context);
    }
  }

  getFallbackResources(context) {
    const subject = context?.subject || 'general';
    const level = context?.level || 'primary';

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
        },
        {
          title: 'Khan Academy Math',
          description: 'Free math practice and video lessons',
          url: 'https://www.khanacademy.org/math',
          type: 'Video Lessons',
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
        },
        {
          title: 'National Geographic Kids',
          description: 'Science facts, experiments, and discoveries',
          url: 'https://kids.nationalgeographic.com/science',
          type: 'Exploration',
          level: 'Primary',
          subject: 'science'
        }
      ],
      english: [
        {
          title: 'Cambridge Primary English',
          description: 'Official Cambridge English curriculum resources',
          url: 'https://www.cambridge.org/gb/education/subject/english/cambridge-primary-english',
          type: 'Curriculum',
          level: 'Primary',
          subject: 'english'
        },
        {
          title: 'BBC Bitesize English',
          description: 'Reading, writing, and grammar activities',
          url: 'https://www.bbc.co.uk/bitesize/subjects/z3c8wmn',
          type: 'Interactive',
          level: 'Primary',
          subject: 'english'
        },
        {
          title: 'Oxford Owl',
          description: 'Free reading books and phonics activities',
          url: 'https://www.oxfordowl.co.uk/',
          type: 'Reading',
          level: 'Primary',
          subject: 'english'
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
        },
        {
          title: 'Duolingo for Schools',
          description: 'Gamified language learning platform',
          url: 'https://schools.duolingo.com/',
          type: 'Gamified Learning',
          level: 'Primary',
          subject: 'esl'
        }
      ]
    };

    const subjectResources = resourceMap[subject] || [];
    const generalResources = [
      {
        title: 'BBC Bitesize Primary',
        description: 'Comprehensive primary education resources',
        url: 'https://www.bbc.co.uk/bitesize/primary',
        type: 'Multi-subject',
        level: 'Primary',
        subject: 'general'
      },
      {
        title: 'Education.com',
        description: 'Worksheets, games, and lesson plans',
        url: 'https://www.education.com/',
        type: 'Practice',
        level: 'Primary',
        subject: 'general'
      }
    ];

    return {
      resources: [...subjectResources, ...generalResources].slice(0, 6)
    };
  }
}

// Initialize background script
new ExtensionBackground();