module.exports = {
  // Use jsdom test environment for DOM manipulation
  testEnvironment: 'jsdom',

  // Setup files after test environment
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],

  // Module path mapping for TypeScript imports
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@selph/shared$': '<rootDir>/../shared/src/index.ts',
  },

  // Transform files
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', {
      tsconfig: {
        jsx: 'react-jsx',
      },
    }],
  },

  // Test file patterns
  testMatch: [
    '<rootDir>/tests/**/*.test.ts',
    '<rootDir>/tests/**/*.test.tsx',
  ],

  // Module file extensions
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],

  // Coverage options
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/index.ts',
    '!src/index.tsx',
  ],

  coverageThreshold: {
    global: {
      branches: 50,
      functions: 50,
      lines: 50,
      statements: 50,
    },
  },

  // Test timeout
  testTimeout: 10000,

  // Verbose output
  verbose: true,
}
