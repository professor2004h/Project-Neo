/**
 * Jest setup file for Chrome Extension tests
 */

// Mock Chrome Extension APIs globally
global.chrome = {
  runtime: {
    onInstalled: { addListener: jest.fn() },
    onMessage: { addListener: jest.fn() },
    sendMessage: jest.fn(),
    getURL: jest.fn((path) => `chrome-extension://test/${path}`),
    id: 'test-extension-id'
  },
  tabs: {
    onActivated: { addListener: jest.fn() },
    onUpdated: { addListener: jest.fn() },
    get: jest.fn(),
    create: jest.fn(),
    query: jest.fn(),
    sendMessage: jest.fn()
  },
  contextMenus: {
    create: jest.fn(),
    onClicked: { addListener: jest.fn() },
    removeAll: jest.fn()
  },
  scripting: {
    executeScript: jest.fn()
  },
  storage: {
    sync: {
      get: jest.fn(),
      set: jest.fn(),
      remove: jest.fn(),
      clear: jest.fn()
    },
    local: {
      get: jest.fn(),
      set: jest.fn(),
      remove: jest.fn(),
      clear: jest.fn()
    }
  },
  action: {
    setBadgeText: jest.fn(),
    setBadgeBackgroundColor: jest.fn()
  }
};

// Mock fetch globally
global.fetch = jest.fn();

// Mock DOM APIs
global.MutationObserver = jest.fn().mockImplementation((callback) => ({
  observe: jest.fn(),
  disconnect: jest.fn(),
  takeRecords: jest.fn()
}));

// Mock console methods to avoid noise in tests
global.console = {
  ...console,
  log: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
  info: jest.fn()
};

// Reset all mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
  
  // Reset fetch mock
  fetch.mockClear();
  
  // Reset Chrome API mocks
  Object.values(chrome).forEach(api => {
    if (typeof api === 'object' && api !== null) {
      Object.values(api).forEach(method => {
        if (typeof method === 'function' && method.mockClear) {
          method.mockClear();
        }
        if (typeof method === 'object' && method !== null && method.addListener) {
          if (method.addListener.mockClear) {
            method.addListener.mockClear();
          }
        }
      });
    }
  });
});

// Helper functions for tests
global.createMockTab = (overrides = {}) => ({
  id: 1,
  url: 'https://example.com',
  title: 'Test Page',
  active: true,
  ...overrides
});

global.createMockAuthResponse = (authenticated = true, profile = null) => ({
  authenticated,
  profile: profile || (authenticated ? { name: 'Test User', role: 'parent' } : null)
});

global.createMockContentResponse = (content = {}) => ({
  content: {
    title: 'Test Page',
    url: 'https://example.com',
    headings: [],
    paragraphs: [],
    mathContent: [],
    exercises: [],
    vocabulary: [],
    ...content
  }
});

// Mock window and document for popup tests
global.window = {
  close: jest.fn(),
  location: {
    href: 'chrome-extension://test/popup.html'
  }
};

global.document = {
  getElementById: jest.fn(),
  querySelector: jest.fn(),
  querySelectorAll: jest.fn(() => []),
  createElement: jest.fn(() => ({
    addEventListener: jest.fn(),
    appendChild: jest.fn(),
    setAttribute: jest.fn(),
    style: {},
    classList: {
      add: jest.fn(),
      remove: jest.fn(),
      contains: jest.fn()
    }
  })),
  addEventListener: jest.fn(),
  body: {
    appendChild: jest.fn()
  },
  head: {
    appendChild: jest.fn()
  },
  title: 'Test Page',
  readyState: 'complete'
};