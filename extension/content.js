/**
 * Cambridge AI Tutor Chrome Extension - Content Script
 * Handles educational website integration and context-aware help
 */

class TutorContentScript {
  constructor() {
    this.isInjected = false;
    this.tutorWidget = null;
    this.helpButton = null;
    this.currentContext = null;
    this.educationalContent = [];
    
    this.init();
  }

  init() {
    // Prevent multiple injections
    if (window.cambridgeAITutorInjected) {
      return;
    }
    window.cambridgeAITutorInjected = true;

    // Set up message listener
    chrome.runtime.onMessage.addListener(this.handleMessage.bind(this));
    
    // Analyze page content
    this.analyzePageContent();
    
    // Inject help interface if educational content is detected
    this.injectHelpInterface();
    
    // Set up content monitoring
    this.setupContentMonitoring();
    
    console.log('Cambridge AI Tutor content script initialized');
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
        
      case 'highlightContent':
        this.highlightEducationalContent(request.content);
        break;
        
      default:
        sendResponse({ error: 'Unknown action' });
    }
    
    return true;
  }

  analyzePageContent() {
    const content = this.extractPageContent();
    const url = window.location.href;
    
    // Perform local analysis first
    const localAnalysis = this.performLocalAnalysis(content, url);
    
    // Send content to background script for enhanced analysis
    chrome.runtime.sendMessage({
      action: 'analyzeContent',
      content,
      url,
      localAnalysis
    }, (response) => {
      if (response && response.educational) {
        this.currentContext = response;
        this.identifyEducationalElements();
        this.updateBookmarkStatus();
      } else if (localAnalysis.educational) {
        // Use local analysis if backend analysis fails
        this.currentContext = localAnalysis;
        this.identifyEducationalElements();
        this.updateBookmarkStatus();
      }
    });
  }

  performLocalAnalysis(content, url) {
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
      'khanacademy.org': { subject: 'general', level: 'primary', confidence: 0.8 },
      'mathsisfun.com': { subject: 'mathematics', level: 'primary', confidence: 0.8 },
      'education.com': { subject: 'general', level: 'primary', confidence: 0.7 }
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
      mathematics: [
        'math', 'maths', 'arithmetic', 'algebra', 'geometry', 'fraction', 'decimal',
        'multiplication', 'division', 'addition', 'subtraction', 'equation', 'number',
        'calculate', 'solve', 'problem', 'formula', 'graph', 'chart'
      ],
      science: [
        'science', 'biology', 'chemistry', 'physics', 'experiment', 'hypothesis',
        'observation', 'theory', 'atom', 'molecule', 'energy', 'force', 'gravity',
        'plant', 'animal', 'ecosystem', 'environment'
      ],
      english: [
        'english', 'grammar', 'vocabulary', 'spelling', 'reading', 'writing',
        'comprehension', 'literature', 'story', 'poem', 'essay', 'sentence',
        'paragraph', 'verb', 'noun', 'adjective', 'pronunciation'
      ],
      esl: [
        'esl', 'english as second language', 'pronunciation', 'phonics',
        'speaking', 'listening', 'conversation', 'accent', 'fluency'
      ]
    };

    // Educational content indicators
    const educationalIndicators = [
      'lesson', 'learn', 'study', 'practice', 'exercise', 'quiz', 'test',
      'homework', 'assignment', 'curriculum', 'grade', 'level', 'skill',
      'knowledge', 'understand', 'explain', 'example', 'definition'
    ];

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

    // Check for educational indicators
    const educationalScore = educationalIndicators.reduce((count, indicator) => {
      const titleMatches = (titleText.match(new RegExp(indicator, 'g')) || []).length * 2;
      const textMatches = (allText.match(new RegExp(indicator, 'g')) || []).length;
      return count + titleMatches + textMatches;
    }, 0);

    // Determine if content is educational
    if (!analysis.educational && (maxSubjectScore > 3 || educationalScore > 5)) {
      analysis.educational = true;
      analysis.subject = detectedSubject || 'general';
      analysis.confidence = Math.min(0.8, (maxSubjectScore + educationalScore) / 20);
    }

    // Level detection based on vocabulary complexity
    if (analysis.educational) {
      const complexWords = allText.split(' ').filter(word => word.length > 8).length;
      const totalWords = allText.split(' ').length;
      const complexityRatio = complexWords / totalWords;

      if (complexityRatio < 0.1) {
        analysis.level = 'primary';
      } else if (complexityRatio < 0.2) {
        analysis.level = 'intermediate';
      } else {
        analysis.level = 'advanced';
      }
    }

    // Extract topics from headings and key content
    if (analysis.educational) {
      analysis.topics = content.headings
        .filter(h => h.text.length > 5 && h.text.length < 100)
        .map(h => h.text.trim())
        .slice(0, 5); // Limit to top 5 topics
    }

    return analysis;
  }

  extractPageContent() {
    // Extract relevant educational content from the page
    const content = {
      title: document.title,
      url: window.location.href,
      headings: this.extractHeadings(),
      paragraphs: this.extractParagraphs(),
      mathContent: this.extractMathContent(),
      exercises: this.extractExercises(),
      vocabulary: this.extractVocabulary()
    };
    
    return content;
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
    const paragraphElements = document.querySelectorAll('p, .content, .description, .explanation');
    
    paragraphElements.forEach(p => {
      const text = p.textContent.trim();
      if (text.length > 50) { // Filter out short paragraphs
        paragraphs.push({
          text,
          element: p
        });
      }
    });
    
    return paragraphs;
  }

  extractMathContent() {
    const mathElements = [];
    
    // Look for MathJax, KaTeX, or math-specific content
    const mathSelectors = [
      '.MathJax',
      '.katex',
      '.math',
      '[data-math]',
      '.equation',
      '.formula'
    ];
    
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
    
    // Look for exercise-like content
    const exerciseSelectors = [
      '.exercise',
      '.question',
      '.problem',
      '.activity',
      '[data-exercise]',
      '.quiz-question'
    ];
    
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
    
    // Look for vocabulary or key terms
    const vocabSelectors = [
      '.vocabulary',
      '.key-term',
      '.definition',
      '.glossary-term',
      'strong',
      'em',
      '.highlight'
    ];
    
    vocabSelectors.forEach(selector => {
      document.querySelectorAll(selector).forEach(element => {
        const text = element.textContent.trim();
        if (text.length > 2 && text.length < 50) {
          vocabulary.push({
            term: text,
            element
          });
        }
      });
    });
    
    return vocabulary;
  }

  identifyEducationalElements() {
    // Add visual indicators to educational content
    this.educationalContent.forEach(item => {
      if (item.element) {
        item.element.classList.add('tutor-educational-content');
        item.element.addEventListener('click', (e) => {
          this.handleEducationalContentClick(e, item);
        });
      }
    });
  }

  injectHelpInterface() {
    // Create floating help button
    this.createHelpButton();
    
    // Create tutor widget (initially hidden)
    this.createTutorWidget();
    
    // Add CSS styles
    this.injectStyles();
  }

  createHelpButton() {
    this.helpButton = document.createElement('div');
    this.helpButton.id = 'cambridge-tutor-help-btn';
    this.helpButton.innerHTML = `
      <div class="help-btn-icon">?</div>
      <div class="help-btn-text">AI Tutor</div>
    `;
    
    this.helpButton.addEventListener('click', () => {
      this.toggleTutorWidget();
    });
    
    document.body.appendChild(this.helpButton);
  }

  createTutorWidget() {
    this.tutorWidget = document.createElement('div');
    this.tutorWidget.id = 'cambridge-tutor-widget';
    this.tutorWidget.innerHTML = `
      <div class="widget-header">
        <h3>Cambridge AI Tutor</h3>
        <div class="header-actions">
          <button class="bookmark-btn" id="tutor-bookmark-btn" title="Bookmark this page">⭐</button>
          <button class="close-btn" id="tutor-close-btn">×</button>
        </div>
      </div>
      <div class="widget-content">
        <div class="context-info" id="tutor-context"></div>
        <div class="widget-tabs">
          <button class="tab-btn active" data-tab="chat">Chat</button>
          <button class="tab-btn" data-tab="bookmarks">Bookmarks</button>
          <button class="tab-btn" data-tab="resources">Resources</button>
        </div>
        <div class="tab-content active" id="chat-tab">
          <div class="chat-area" id="tutor-chat">
            <div class="welcome-message">
              Hi! I'm your AI tutor. I can help explain concepts on this page or answer your questions.
            </div>
          </div>
          <div class="input-area">
            <input type="text" id="tutor-input" placeholder="Ask me anything about this page...">
            <button id="tutor-send-btn">Send</button>
          </div>
        </div>
        <div class="tab-content" id="bookmarks-tab">
          <div class="bookmarks-header">
            <h4>Educational Bookmarks</h4>
            <button id="clear-bookmarks-btn" class="small-btn">Clear All</button>
          </div>
          <div class="bookmarks-list" id="bookmarks-list">
            <div class="empty-state">No bookmarks yet. Bookmark educational pages to access them later!</div>
          </div>
        </div>
        <div class="tab-content" id="resources-tab">
          <div class="resources-header">
            <h4>Related Resources</h4>
            <button id="refresh-resources-btn" class="small-btn">Refresh</button>
          </div>
          <div class="resources-list" id="resources-list">
            <div class="loading-resources">Loading related resources...</div>
          </div>
        </div>
      </div>
    `;
    
    // Set up event listeners
    this.tutorWidget.querySelector('#tutor-close-btn').addEventListener('click', () => {
      this.hideTutorWidget();
    });
    
    this.tutorWidget.querySelector('#tutor-bookmark-btn').addEventListener('click', () => {
      this.toggleBookmark();
    });
    
    this.tutorWidget.querySelector('#tutor-send-btn').addEventListener('click', () => {
      this.sendQuestion();
    });
    
    this.tutorWidget.querySelector('#tutor-input').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.sendQuestion();
      }
    });

    // Tab switching
    this.tutorWidget.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        this.switchTab(e.target.dataset.tab);
      });
    });

    // Bookmark management
    this.tutorWidget.querySelector('#clear-bookmarks-btn').addEventListener('click', () => {
      this.clearAllBookmarks();
    });

    // Resources refresh
    this.tutorWidget.querySelector('#refresh-resources-btn').addEventListener('click', () => {
      this.loadRelatedResources();
    });
    
    document.body.appendChild(this.tutorWidget);
  }

  injectStyles() {
    const style = document.createElement('style');
    style.textContent = `
      #cambridge-tutor-help-btn {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        background: #4CAF50;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        transition: all 0.3s ease;
        color: white;
        font-family: Arial, sans-serif;
      }
      
      #cambridge-tutor-help-btn:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 16px rgba(0,0,0,0.2);
      }
      
      .help-btn-icon {
        font-size: 24px;
        font-weight: bold;
      }
      
      .help-btn-text {
        font-size: 8px;
        margin-top: 2px;
      }
      
      #cambridge-tutor-widget {
        position: fixed;
        bottom: 90px;
        right: 20px;
        width: 350px;
        height: 450px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.15);
        z-index: 10001;
        display: none;
        flex-direction: column;
        font-family: Arial, sans-serif;
        border: 1px solid #e0e0e0;
      }
      
      .widget-header {
        background: #4CAF50;
        color: white;
        padding: 15px;
        border-radius: 12px 12px 0 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .widget-header h3 {
        margin: 0;
        font-size: 16px;
        flex: 1;
      }

      .header-actions {
        display: flex;
        gap: 8px;
        align-items: center;
      }
      
      .bookmark-btn, .close-btn {
        background: none;
        border: none;
        color: white;
        font-size: 18px;
        cursor: pointer;
        padding: 4px;
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
        transition: background-color 0.2s;
      }

      .bookmark-btn:hover, .close-btn:hover {
        background: rgba(255, 255, 255, 0.2);
      }

      .bookmark-btn.bookmarked {
        color: #FFD700;
      }
      
      .widget-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        padding: 15px;
      }
      
      .context-info {
        background: #f5f5f5;
        padding: 10px;
        border-radius: 6px;
        margin-bottom: 15px;
        font-size: 12px;
        color: #666;
      }
      
      .chat-area {
        flex: 1;
        overflow-y: auto;
        margin-bottom: 15px;
        padding: 10px;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        background: #fafafa;
      }
      
      .welcome-message {
        color: #666;
        font-style: italic;
        text-align: center;
        padding: 20px;
      }
      
      .message {
        margin-bottom: 10px;
        padding: 8px 12px;
        border-radius: 6px;
        max-width: 80%;
      }
      
      .message.user {
        background: #e3f2fd;
        margin-left: auto;
        text-align: right;
      }
      
      .message.tutor {
        background: #f1f8e9;
        margin-right: auto;
      }
      
      .input-area {
        display: flex;
        gap: 10px;
      }
      
      #tutor-input {
        flex: 1;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 6px;
        font-size: 14px;
      }
      
      #tutor-send-btn {
        background: #4CAF50;
        color: white;
        border: none;
        padding: 10px 15px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 14px;
      }
      
      #tutor-send-btn:hover {
        background: #45a049;
      }
      
      .tutor-educational-content {
        position: relative;
        cursor: help;
      }
      
      .tutor-educational-content:hover {
        background-color: rgba(76, 175, 80, 0.1);
      }
      
      .tutor-highlight {
        background-color: rgba(255, 235, 59, 0.3);
        padding: 2px 4px;
        border-radius: 3px;
      }

      .widget-tabs {
        display: flex;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 15px;
      }

      .tab-btn {
        flex: 1;
        background: none;
        border: none;
        padding: 10px;
        cursor: pointer;
        font-size: 12px;
        color: #666;
        border-bottom: 2px solid transparent;
        transition: all 0.2s;
      }

      .tab-btn.active {
        color: #4CAF50;
        border-bottom-color: #4CAF50;
        font-weight: 500;
      }

      .tab-btn:hover {
        background: #f5f5f5;
      }

      .tab-content {
        display: none;
      }

      .tab-content.active {
        display: block;
      }

      .bookmarks-header, .resources-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
      }

      .bookmarks-header h4, .resources-header h4 {
        margin: 0;
        font-size: 14px;
        color: #333;
      }

      .small-btn {
        background: #f5f5f5;
        border: 1px solid #ddd;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 11px;
        cursor: pointer;
        color: #666;
      }

      .small-btn:hover {
        background: #e0e0e0;
      }

      .bookmarks-list, .resources-list {
        max-height: 200px;
        overflow-y: auto;
      }

      .bookmark-item, .resource-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 8px;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        margin-bottom: 8px;
        background: white;
        transition: background-color 0.2s;
      }

      .bookmark-item:hover, .resource-item:hover {
        background: #f8f9fa;
      }

      .bookmark-favicon {
        position: relative;
        width: 20px;
        height: 20px;
        flex-shrink: 0;
      }

      .bookmark-favicon img {
        width: 16px;
        height: 16px;
        border-radius: 2px;
      }

      .bookmark-subject {
        position: absolute;
        bottom: -2px;
        right: -2px;
        font-size: 10px;
        background: white;
        border-radius: 50%;
        width: 14px;
        height: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
      }

      .bookmark-content, .resource-content {
        flex: 1;
        min-width: 0;
      }

      .bookmark-title, .resource-title {
        font-size: 12px;
        font-weight: 500;
        color: #333;
        margin-bottom: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .bookmark-meta, .resource-meta {
        display: flex;
        gap: 8px;
        font-size: 10px;
        color: #666;
        margin-bottom: 4px;
      }

      .bookmark-topics {
        display: flex;
        gap: 4px;
        flex-wrap: wrap;
      }

      .topic-tag {
        background: #e3f2fd;
        color: #1976d2;
        padding: 2px 6px;
        border-radius: 10px;
        font-size: 9px;
        font-weight: 500;
      }

      .bookmark-actions, .resource-actions {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }

      .bookmark-action-btn, .resource-action-btn {
        background: none;
        border: 1px solid #ddd;
        padding: 4px 6px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 10px;
        color: #666;
        transition: all 0.2s;
      }

      .bookmark-action-btn:hover, .resource-action-btn:hover {
        background: #f0f0f0;
        border-color: #4CAF50;
        color: #4CAF50;
      }

      .resource-icon {
        font-size: 16px;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
      }

      .resource-description {
        font-size: 11px;
        color: #666;
        margin-bottom: 4px;
        line-height: 1.3;
      }

      .empty-state, .error-state, .loading-resources {
        text-align: center;
        padding: 20px;
        color: #666;
        font-size: 12px;
        font-style: italic;
      }

      .tutor-notification {
        animation: slideIn 0.3s ease;
      }

      @keyframes slideIn {
        from {
          transform: translateX(100%);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }

      @keyframes slideOut {
        from {
          transform: translateX(0);
          opacity: 1;
        }
        to {
          transform: translateX(100%);
          opacity: 0;
        }
      }
    `;
    
    document.head.appendChild(style);
  }

  setupContentMonitoring() {
    // Monitor for dynamic content changes
    const observer = new MutationObserver((mutations) => {
      let shouldReanalyze = false;
      
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
          // Check if new educational content was added
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              const hasEducationalContent = node.querySelector && (
                node.querySelector('.exercise, .question, .math, .vocabulary') ||
                node.textContent.length > 100
              );
              
              if (hasEducationalContent) {
                shouldReanalyze = true;
              }
            }
          });
        }
      });
      
      if (shouldReanalyze) {
        setTimeout(() => this.analyzePageContent(), 1000);
      }
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  toggleTutorWidget() {
    if (this.tutorWidget.style.display === 'none' || !this.tutorWidget.style.display) {
      this.showTutorWidget();
    } else {
      this.hideTutorWidget();
    }
  }

  showTutorWidget() {
    this.tutorWidget.style.display = 'flex';
    this.updateContextInfo();
    
    // Track widget opening
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

  updateContextInfo() {
    const contextDiv = this.tutorWidget.querySelector('#tutor-context');
    if (this.currentContext && this.currentContext.educational) {
      contextDiv.innerHTML = `
        <strong>Page Context:</strong> ${this.currentContext.subject || 'Educational content'} detected<br>
        <strong>Level:</strong> ${this.currentContext.level || 'Auto-detected'}
      `;
    } else {
      contextDiv.innerHTML = '<strong>Context:</strong> General help available';
    }
  }

  async sendQuestion() {
    const input = this.tutorWidget.querySelector('#tutor-input');
    const question = input.value.trim();
    
    if (!question) return;
    
    // Add user message to chat
    this.addMessageToChat(question, 'user');
    input.value = '';
    
    // Show typing indicator
    this.showTypingIndicator();
    
    try {
      // Send question to background script
      const context = {
        pageContent: this.extractPageContent(),
        currentContext: this.currentContext
      };
      
      chrome.runtime.sendMessage({
        action: 'askQuestion',
        question,
        context
      }, (response) => {
        this.hideTypingIndicator();
        
        if (response && response.answer) {
          this.addMessageToChat(response.answer, 'tutor');
          
          // Track question asked
          chrome.runtime.sendMessage({
            action: 'trackActivity',
            activity: {
              type: 'question_asked',
              question,
              url: window.location.href,
              context: this.currentContext
            }
          });
        } else {
          this.addMessageToChat('Sorry, I encountered an error. Please try again.', 'tutor');
        }
      });
    } catch (error) {
      this.hideTypingIndicator();
      this.addMessageToChat('Sorry, I encountered an error. Please try again.', 'tutor');
      console.error('Question sending failed:', error);
    }
  }

  addMessageToChat(message, sender) {
    const chatArea = this.tutorWidget.querySelector('#tutor-chat');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    messageDiv.textContent = message;
    
    // Remove welcome message if it exists
    const welcomeMessage = chatArea.querySelector('.welcome-message');
    if (welcomeMessage) {
      welcomeMessage.remove();
    }
    
    chatArea.appendChild(messageDiv);
    chatArea.scrollTop = chatArea.scrollHeight;
  }

  showTypingIndicator() {
    const chatArea = this.tutorWidget.querySelector('#tutor-chat');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message tutor typing-indicator';
    typingDiv.innerHTML = 'Thinking...';
    typingDiv.id = 'typing-indicator';
    
    chatArea.appendChild(typingDiv);
    chatArea.scrollTop = chatArea.scrollHeight;
  }

  hideTypingIndicator() {
    const typingIndicator = this.tutorWidget.querySelector('#typing-indicator');
    if (typingIndicator) {
      typingIndicator.remove();
    }
  }

  showExplanation(explanation, selectedText) {
    this.showTutorWidget();
    this.addMessageToChat(`You selected: "${selectedText}"`, 'user');
    this.addMessageToChat(explanation.answer || explanation, 'tutor');
  }

  showPageHelp(analysis) {
    this.showTutorWidget();
    
    if (analysis && analysis.educational) {
      const helpMessage = `I can help you with this ${analysis.subject || 'educational'} content. What would you like to know?`;
      this.addMessageToChat(helpMessage, 'tutor');
      
      if (analysis.suggestions && analysis.suggestions.length > 0) {
        const suggestionsMessage = `Here are some things I can help with:\n${analysis.suggestions.join('\n')}`;
        this.addMessageToChat(suggestionsMessage, 'tutor');
      }
    } else {
      this.addMessageToChat('I can help answer questions about this page. What would you like to know?', 'tutor');
    }
  }

  handleEducationalContentClick(event, item) {
    event.preventDefault();
    
    // Show explanation for the clicked educational content
    const question = `Can you explain this: ${item.content || item.text}`;
    this.showTutorWidget();
    this.addMessageToChat(question, 'user');
    
    // Auto-send the question
    const input = this.tutorWidget.querySelector('#tutor-input');
    input.value = question;
    this.sendQuestion();
  }

  highlightEducationalContent(content) {
    // Highlight specific content on the page
    content.forEach(item => {
      if (item.element) {
        item.element.classList.add('tutor-highlight');
        setTimeout(() => {
          item.element.classList.remove('tutor-highlight');
        }, 3000);
      }
    });
  }

  // Bookmark Management Methods
  async toggleBookmark() {
    const currentPage = {
      url: window.location.href,
      title: document.title,
      subject: this.currentContext?.subject || 'general',
      level: this.currentContext?.level || 'unknown',
      topics: this.currentContext?.topics || [],
      timestamp: new Date().toISOString(),
      favicon: this.getFavicon()
    };

    try {
      const bookmarks = await this.getBookmarks();
      const existingIndex = bookmarks.findIndex(b => b.url === currentPage.url);
      
      if (existingIndex >= 0) {
        // Remove bookmark
        bookmarks.splice(existingIndex, 1);
        this.updateBookmarkButton(false);
        this.showNotification('Bookmark removed');
      } else {
        // Add bookmark
        bookmarks.unshift(currentPage);
        // Keep only last 50 bookmarks
        if (bookmarks.length > 50) {
          bookmarks.splice(50);
        }
        this.updateBookmarkButton(true);
        this.showNotification('Page bookmarked');
      }

      await this.saveBookmarks(bookmarks);
      this.refreshBookmarksList();
      
      // Track bookmark activity
      chrome.runtime.sendMessage({
        action: 'trackActivity',
        activity: {
          type: existingIndex >= 0 ? 'bookmark_removed' : 'bookmark_added',
          url: currentPage.url,
          title: currentPage.title,
          subject: currentPage.subject
        }
      });
    } catch (error) {
      console.error('Bookmark toggle failed:', error);
      this.showNotification('Failed to update bookmark');
    }
  }

  async updateBookmarkStatus() {
    try {
      const bookmarks = await this.getBookmarks();
      const isBookmarked = bookmarks.some(b => b.url === window.location.href);
      this.updateBookmarkButton(isBookmarked);
    } catch (error) {
      console.error('Failed to update bookmark status:', error);
    }
  }

  updateBookmarkButton(isBookmarked) {
    const bookmarkBtn = this.tutorWidget.querySelector('#tutor-bookmark-btn');
    if (bookmarkBtn) {
      bookmarkBtn.textContent = isBookmarked ? '⭐' : '☆';
      bookmarkBtn.title = isBookmarked ? 'Remove bookmark' : 'Bookmark this page';
      bookmarkBtn.classList.toggle('bookmarked', isBookmarked);
    }
  }

  async getBookmarks() {
    return new Promise((resolve) => {
      chrome.storage.sync.get(['educationalBookmarks'], (result) => {
        resolve(result.educationalBookmarks || []);
      });
    });
  }

  async saveBookmarks(bookmarks) {
    return new Promise((resolve) => {
      chrome.storage.sync.set({ educationalBookmarks: bookmarks }, resolve);
    });
  }

  async clearAllBookmarks() {
    if (confirm('Are you sure you want to clear all bookmarks?')) {
      await this.saveBookmarks([]);
      this.refreshBookmarksList();
      this.updateBookmarkButton(false);
      this.showNotification('All bookmarks cleared');
    }
  }

  async refreshBookmarksList() {
    const bookmarksList = this.tutorWidget.querySelector('#bookmarks-list');
    if (!bookmarksList) return;

    try {
      const bookmarks = await this.getBookmarks();
      
      if (bookmarks.length === 0) {
        bookmarksList.innerHTML = '<div class="empty-state">No bookmarks yet. Bookmark educational pages to access them later!</div>';
        return;
      }

      bookmarksList.innerHTML = bookmarks.map(bookmark => `
        <div class="bookmark-item" data-url="${bookmark.url}">
          <div class="bookmark-favicon">
            <img src="${bookmark.favicon}" alt="" onerror="this.style.display='none'">
            <span class="bookmark-subject">${this.getSubjectIcon(bookmark.subject)}</span>
          </div>
          <div class="bookmark-content">
            <div class="bookmark-title">${bookmark.title}</div>
            <div class="bookmark-meta">
              <span class="bookmark-subject-text">${bookmark.subject}</span>
              <span class="bookmark-level">${bookmark.level}</span>
              <span class="bookmark-date">${this.formatDate(bookmark.timestamp)}</span>
            </div>
            ${bookmark.topics.length > 0 ? `
              <div class="bookmark-topics">
                ${bookmark.topics.slice(0, 3).map(topic => `<span class="topic-tag">${topic}</span>`).join('')}
              </div>
            ` : ''}
          </div>
          <div class="bookmark-actions">
            <button class="bookmark-action-btn" onclick="window.open('${bookmark.url}', '_blank')" title="Open">🔗</button>
            <button class="bookmark-action-btn" onclick="this.closest('.bookmark-item').remove(); window.tutorContentScript.removeBookmark('${bookmark.url}')" title="Remove">🗑️</button>
          </div>
        </div>
      `).join('');
    } catch (error) {
      console.error('Failed to refresh bookmarks list:', error);
      bookmarksList.innerHTML = '<div class="error-state">Failed to load bookmarks</div>';
    }
  }

  async removeBookmark(url) {
    try {
      const bookmarks = await this.getBookmarks();
      const filteredBookmarks = bookmarks.filter(b => b.url !== url);
      await this.saveBookmarks(filteredBookmarks);
      
      if (url === window.location.href) {
        this.updateBookmarkButton(false);
      }
      
      this.showNotification('Bookmark removed');
    } catch (error) {
      console.error('Failed to remove bookmark:', error);
    }
  }

  getFavicon() {
    const favicon = document.querySelector('link[rel="icon"], link[rel="shortcut icon"]');
    return favicon ? favicon.href : `${window.location.origin}/favicon.ico`;
  }

  getSubjectIcon(subject) {
    const icons = {
      mathematics: '🔢',
      science: '🔬',
      english: '📚',
      esl: '🗣️',
      general: '📖'
    };
    return icons[subject] || icons.general;
  }

  formatDate(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  }

  // Tab Management
  switchTab(tabName) {
    // Update tab buttons
    this.tutorWidget.querySelectorAll('.tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Update tab content
    this.tutorWidget.querySelectorAll('.tab-content').forEach(content => {
      content.classList.toggle('active', content.id === `${tabName}-tab`);
    });

    // Load content for specific tabs
    if (tabName === 'bookmarks') {
      this.refreshBookmarksList();
    } else if (tabName === 'resources') {
      this.loadRelatedResources();
    }
  }

  async loadRelatedResources() {
    const resourcesList = this.tutorWidget.querySelector('#resources-list');
    if (!resourcesList) return;

    resourcesList.innerHTML = '<div class="loading-resources">Loading related resources...</div>';

    try {
      // Get related resources based on current context
      const response = await chrome.runtime.sendMessage({
        action: 'getRelatedResources',
        context: this.currentContext,
        url: window.location.href
      });

      if (response && response.resources && response.resources.length > 0) {
        resourcesList.innerHTML = response.resources.map(resource => `
          <div class="resource-item">
            <div class="resource-icon">${this.getSubjectIcon(resource.subject)}</div>
            <div class="resource-content">
              <div class="resource-title">${resource.title}</div>
              <div class="resource-description">${resource.description}</div>
              <div class="resource-meta">
                <span class="resource-type">${resource.type}</span>
                <span class="resource-level">${resource.level}</span>
              </div>
            </div>
            <div class="resource-actions">
              <button class="resource-action-btn" onclick="window.open('${resource.url}', '_blank')">Open</button>
            </div>
          </div>
        `).join('');
      } else {
        // Show default educational resources
        this.showDefaultResources(resourcesList);
      }
    } catch (error) {
      console.error('Failed to load related resources:', error);
      this.showDefaultResources(resourcesList);
    }
  }

  showDefaultResources(container) {
    const defaultResources = [
      {
        title: 'Cambridge Primary Mathematics',
        description: 'Official Cambridge mathematics curriculum resources',
        url: 'https://www.cambridge.org/gb/education/subject/mathematics/cambridge-primary-mathematics',
        type: 'Curriculum',
        level: 'Primary',
        subject: 'mathematics'
      },
      {
        title: 'BBC Bitesize Primary',
        description: 'Interactive lessons and activities for primary students',
        url: 'https://www.bbc.co.uk/bitesize/primary',
        type: 'Interactive',
        level: 'Primary',
        subject: 'general'
      },
      {
        title: 'Khan Academy Kids',
        description: 'Free educational content for young learners',
        url: 'https://www.khanacademy.org/kids',
        type: 'Practice',
        level: 'Primary',
        subject: 'general'
      }
    ];

    container.innerHTML = defaultResources.map(resource => `
      <div class="resource-item">
        <div class="resource-icon">${this.getSubjectIcon(resource.subject)}</div>
        <div class="resource-content">
          <div class="resource-title">${resource.title}</div>
          <div class="resource-description">${resource.description}</div>
          <div class="resource-meta">
            <span class="resource-type">${resource.type}</span>
            <span class="resource-level">${resource.level}</span>
          </div>
        </div>
        <div class="resource-actions">
          <button class="resource-action-btn" onclick="window.open('${resource.url}', '_blank')">Open</button>
        </div>
      </div>
    `).join('');
  }

  showNotification(message) {
    // Create a temporary notification
    const notification = document.createElement('div');
    notification.className = 'tutor-notification';
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #4CAF50;
      color: white;
      padding: 12px 16px;
      border-radius: 6px;
      z-index: 10002;
      font-family: Arial, sans-serif;
      font-size: 14px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
      notification.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }, 3000);
  }
}

// Initialize content script when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.tutorContentScript = new TutorContentScript();
  });
} else {
  window.tutorContentScript = new TutorContentScript();
}