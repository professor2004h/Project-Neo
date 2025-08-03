/**
 * Unit tests for Chrome Extension Content Script
 */

// Mock Chrome APIs
global.chrome = {
  runtime: {
    onMessage: { addListener: jest.fn() },
    sendMessage: jest.fn()
  }
};

// Mock DOM
global.document = {
  title: 'Test Page',
  body: document.createElement('body'),
  head: document.createElement('head'),
  createElement: jest.fn((tag) => document.createElement(tag)),
  querySelector: jest.fn(),
  querySelectorAll: jest.fn(() => []),
  addEventListener: jest.fn(),
  readyState: 'complete'
};

global.window = {
  location: {
    href: 'https://www.cambridge.org/test-page'
  },
  addEventListener: jest.fn()
};

describe('TutorContentScript', () => {
  let TutorContentScript;
  let contentScript;
  let mockElement;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Create mock DOM elements
    mockElement = {
      textContent: 'Test content',
      innerHTML: '<p>Test content</p>',
      classList: {
        add: jest.fn(),
        remove: jest.fn()
      },
      addEventListener: jest.fn(),
      appendChild: jest.fn(),
      querySelector: jest.fn(),
      style: {}
    };

    document.createElement.mockReturnValue(mockElement);
    document.querySelector.mockReturnValue(mockElement);
    document.querySelectorAll.mockReturnValue([mockElement]);

    // Mock content script class
    TutorContentScript = class {
      constructor() {
        this.isInjected = false;
        this.tutorWidget = null;
        this.helpButton = null;
        this.currentContext = null;
        this.educationalContent = [];
        this.init();
      }

      init() {
        if (window.cambridgeAITutorInjected) return;
        window.cambridgeAITutorInjected = true;

        chrome.runtime.onMessage.addListener(this.handleMessage.bind(this));
        this.analyzePageContent();
        this.injectHelpInterface();
        this.setupContentMonitoring();
      }

      handleMessage(request, sender, sendResponse) {
        switch (request.action) {
          case 'getPageContent':
            sendResponse({ content: this.extractPageContent() });
            break;
          case 'showExplanation':
            this.showExplanation(request.explanation, request.selectedText);
            break;
          case 'showPageHelp':
            this.showPageHelp(request.analysis);
            break;
          default:
            sendResponse({ error: 'Unknown action' });
        }
        return true;
      }

      analyzePageContent() {
        const content = this.extractPageContent();
        chrome.runtime.sendMessage({
          action: 'analyzeContent',
          content,
          url: window.location.href
        });
      }

      extractPageContent() {
        return {
          title: document.title,
          url: window.location.href,
          headings: this.extractHeadings(),
          paragraphs: this.extractParagraphs(),
          mathContent: this.extractMathContent(),
          exercises: this.extractExercises(),
          vocabulary: this.extractVocabulary()
        };
      }

      extractHeadings() {
        const headings = [];
        const headingElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        
        headingElements.forEach(heading => {
          headings.push({
            level: parseInt(heading.tagName.charAt(1)),
            text: heading.textContent.trim(),
            element: heading
          });
        });
        
        return headings;
      }

      extractParagraphs() {
        const paragraphs = [];
        const paragraphElements = document.querySelectorAll('p, .content, .description');
        
        paragraphElements.forEach(p => {
          const text = p.textContent.trim();
          if (text.length > 50) {
            paragraphs.push({ text, element: p });
          }
        });
        
        return paragraphs;
      }

      extractMathContent() {
        const mathElements = [];
        const mathSelectors = ['.MathJax', '.katex', '.math'];
        
        mathSelectors.forEach(selector => {
          document.querySelectorAll(selector).forEach(element => {
            mathElements.push({
              content: element.textContent || element.innerHTML,
              element
            });
          });
        });
        
        return mathElements;
      }

      extractExercises() {
        const exercises = [];
        const exerciseSelectors = ['.exercise', '.question', '.problem'];
        
        exerciseSelectors.forEach(selector => {
          document.querySelectorAll(selector).forEach(element => {
            exercises.push({
              content: element.textContent.trim(),
              element
            });
          });
        });
        
        return exercises;
      }

      extractVocabulary() {
        const vocabulary = [];
        const vocabSelectors = ['.vocabulary', '.key-term', 'strong'];
        
        vocabSelectors.forEach(selector => {
          document.querySelectorAll(selector).forEach(element => {
            const text = element.textContent.trim();
            if (text.length > 2 && text.length < 50) {
              vocabulary.push({ term: text, element });
            }
          });
        });
        
        return vocabulary;
      }

      injectHelpInterface() {
        this.createHelpButton();
        this.createTutorWidget();
        this.injectStyles();
      }

      createHelpButton() {
        this.helpButton = document.createElement('div');
        this.helpButton.id = 'cambridge-tutor-help-btn';
        this.helpButton.addEventListener('click', () => {
          this.toggleTutorWidget();
        });
        document.body.appendChild(this.helpButton);
      }

      createTutorWidget() {
        this.tutorWidget = document.createElement('div');
        this.tutorWidget.id = 'cambridge-tutor-widget';
        this.tutorWidget.style.display = 'none';
        document.body.appendChild(this.tutorWidget);
      }

      injectStyles() {
        const style = document.createElement('style');
        document.head.appendChild(style);
      }

      setupContentMonitoring() {
        // Mock MutationObserver
        global.MutationObserver = jest.fn().mockImplementation((callback) => ({
          observe: jest.fn(),
          disconnect: jest.fn()
        }));
        
        const observer = new MutationObserver(() => {});
        observer.observe(document.body, { childList: true, subtree: true });
      }

      toggleTutorWidget() {
        if (this.tutorWidget.style.display === 'none') {
          this.showTutorWidget();
        } else {
          this.hideTutorWidget();
        }
      }

      showTutorWidget() {
        this.tutorWidget.style.display = 'flex';
        chrome.runtime.sendMessage({
          action: 'trackActivity',
          activity: {
            type: 'widget_opened',
            url: window.location.href,
            title: document.title
          }
        });
      }

      hideTutorWidget() {
        this.tutorWidget.style.display = 'none';
      }

      showExplanation(explanation, selectedText) {
        this.showTutorWidget();
        // Mock adding messages to chat
      }

      showPageHelp(analysis) {
        this.showTutorWidget();
        // Mock showing page help
      }
    };

    contentScript = new TutorContentScript();
  });

  describe('Initialization', () => {
    test('should initialize content script without duplicate injection', () => {
      expect(window.cambridgeAITutorInjected).toBe(true);
      expect(chrome.runtime.onMessage.addListener).toHaveBeenCalled();
    });

    test('should prevent multiple injections', () => {
      const secondScript = new TutorContentScript();
      // Should not reinitialize if already injected
      expect(chrome.runtime.onMessage.addListener).toHaveBeenCalledTimes(1);
    });

    test('should set up content monitoring', () => {
      expect(global.MutationObserver).toHaveBeenCalled();
    });
  });

  describe('Message Handling', () => {
    test('should handle getPageContent message', () => {
      const mockSendResponse = jest.fn();
      
      contentScript.handleMessage(
        { action: 'getPageContent' },
        {},
        mockSendResponse
      );

      expect(mockSendResponse).toHaveBeenCalledWith({
        content: expect.objectContaining({
          title: 'Test Page',
          url: 'https://www.cambridge.org/test-page',
          headings: expect.any(Array),
          paragraphs: expect.any(Array),
          mathContent: expect.any(Array),
          exercises: expect.any(Array),
          vocabulary: expect.any(Array)
        })
      });
    });

    test('should handle showExplanation message', () => {
      const showExplanationSpy = jest.spyOn(contentScript, 'showExplanation');
      
      contentScript.handleMessage(
        {
          action: 'showExplanation',
          explanation: 'Test explanation',
          selectedText: 'selected text'
        },
        {},
        jest.fn()
      );

      expect(showExplanationSpy).toHaveBeenCalledWith('Test explanation', 'selected text');
    });

    test('should handle unknown action', () => {
      const mockSendResponse = jest.fn();
      
      contentScript.handleMessage(
        { action: 'unknownAction' },
        {},
        mockSendResponse
      );

      expect(mockSendResponse).toHaveBeenCalledWith({
        error: 'Unknown action'
      });
    });
  });

  describe('Content Extraction', () => {
    test('should extract page content correctly', () => {
      const content = contentScript.extractPageContent();

      expect(content).toEqual({
        title: 'Test Page',
        url: 'https://www.cambridge.org/test-page',
        headings: expect.any(Array),
        paragraphs: expect.any(Array),
        mathContent: expect.any(Array),
        exercises: expect.any(Array),
        vocabulary: expect.any(Array)
      });
    });

    test('should extract headings with correct structure', () => {
      // Mock heading elements
      const mockHeading = {
        tagName: 'H2',
        textContent: '  Test Heading  ',
        trim: jest.fn().mockReturnValue('Test Heading')
      };
      
      document.querySelectorAll.mockReturnValue([mockHeading]);
      
      const headings = contentScript.extractHeadings();
      
      expect(headings).toEqual([{
        level: 2,
        text: 'Test Heading',
        element: mockHeading
      }]);
    });

    test('should filter paragraphs by length', () => {
      const shortParagraph = { textContent: 'Short', trim: () => 'Short' };
      const longParagraph = { 
        textContent: 'This is a long paragraph with more than fifty characters in it',
        trim: () => 'This is a long paragraph with more than fifty characters in it'
      };
      
      document.querySelectorAll.mockReturnValue([shortParagraph, longParagraph]);
      
      const paragraphs = contentScript.extractParagraphs();
      
      expect(paragraphs).toHaveLength(1);
      expect(paragraphs[0].text).toBe('This is a long paragraph with more than fifty characters in it');
    });

    test('should extract math content from various selectors', () => {
      const mathElement = {
        textContent: 'x = 2y + 3',
        innerHTML: '<span>x = 2y + 3</span>'
      };
      
      document.querySelectorAll.mockReturnValue([mathElement]);
      
      const mathContent = contentScript.extractMathContent();
      
      expect(mathContent).toEqual([{
        content: 'x = 2y + 3',
        element: mathElement
      }]);
    });

    test('should extract vocabulary terms within length limits', () => {
      const shortTerm = { textContent: 'a', trim: () => 'a' };
      const validTerm = { textContent: 'photosynthesis', trim: () => 'photosynthesis' };
      const longTerm = { 
        textContent: 'this is a very long term that exceeds the fifty character limit',
        trim: () => 'this is a very long term that exceeds the fifty character limit'
      };
      
      document.querySelectorAll.mockReturnValue([shortTerm, validTerm, longTerm]);
      
      const vocabulary = contentScript.extractVocabulary();
      
      expect(vocabulary).toHaveLength(1);
      expect(vocabulary[0].term).toBe('photosynthesis');
    });
  });

  describe('Help Interface', () => {
    test('should create help button', () => {
      expect(document.createElement).toHaveBeenCalledWith('div');
      expect(mockElement.addEventListener).toHaveBeenCalledWith('click', expect.any(Function));
      expect(document.body.appendChild).toHaveBeenCalled();
    });

    test('should create tutor widget', () => {
      expect(contentScript.tutorWidget).toBeTruthy();
      expect(contentScript.tutorWidget.style.display).toBe('none');
    });

    test('should inject styles', () => {
      expect(document.createElement).toHaveBeenCalledWith('style');
      expect(document.head.appendChild).toHaveBeenCalled();
    });

    test('should toggle widget visibility', () => {
      // Initially hidden
      expect(contentScript.tutorWidget.style.display).toBe('none');
      
      // Toggle to show
      contentScript.toggleTutorWidget();
      expect(contentScript.tutorWidget.style.display).toBe('flex');
      
      // Toggle to hide
      contentScript.toggleTutorWidget();
      expect(contentScript.tutorWidget.style.display).toBe('none');
    });

    test('should track activity when showing widget', () => {
      contentScript.showTutorWidget();
      
      expect(chrome.runtime.sendMessage).toHaveBeenCalledWith({
        action: 'trackActivity',
        activity: {
          type: 'widget_opened',
          url: 'https://www.cambridge.org/test-page',
          title: 'Test Page'
        }
      });
    });
  });

  describe('Page Analysis', () => {
    test('should send content for analysis', () => {
      contentScript.analyzePageContent();
      
      expect(chrome.runtime.sendMessage).toHaveBeenCalledWith({
        action: 'analyzeContent',
        content: expect.objectContaining({
          title: 'Test Page',
          url: 'https://www.cambridge.org/test-page'
        }),
        url: 'https://www.cambridge.org/test-page'
      });
    });
  });

  describe('Educational Content Interaction', () => {
    test('should show explanation when requested', () => {
      const showWidgetSpy = jest.spyOn(contentScript, 'showTutorWidget');
      
      contentScript.showExplanation('Test explanation', 'selected text');
      
      expect(showWidgetSpy).toHaveBeenCalled();
    });

    test('should show page help when requested', () => {
      const showWidgetSpy = jest.spyOn(contentScript, 'showTutorWidget');
      const mockAnalysis = { educational: true, subject: 'math' };
      
      contentScript.showPageHelp(mockAnalysis);
      
      expect(showWidgetSpy).toHaveBeenCalled();
    });
  });
});