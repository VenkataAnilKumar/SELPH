module.exports = {
  // Use jsdom test environment for DOM manipulation
  testEnvironment: 'jsdom',

  // Setup files after test environment
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],

  // Module path mapping for TypeScript imports - order matters, specific first
  moduleNameMapper: {
    '^@/lib/(.*)$': '<rootDir>/lib/$1',
    '^@/components/(.*)$': '<rootDir>/components/$1',
    '^@/app/(.*)$': '<rootDir>/app/$1',
    '^@/(.*)$': '<rootDir>/$1',
    '^@selph/shared$': '<rootDir>/../shared/index.ts',
  },

  // Transform files - Add tsconfig sourceMap
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', {
      tsconfig: {
        jsx: 'react-jsx',
        sourceMap: true,
      },
      useESM: true,
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
