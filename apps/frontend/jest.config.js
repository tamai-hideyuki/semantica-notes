const nextJest = require('next/jest');
const createJestConfig = nextJest({ dir: './' });

const customJestConfig = {
    setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
    testEnvironment: 'jest-environment-jsdom',
    moduleDirectories: ['node_modules', '<rootDir>'],
    transform: {
        '^.+\.(ts|tsx)$': ['ts-jest', { tsconfig: 'tsconfig.json' }]
    },
    transformIgnorePatterns: ['/node_modules/']
};

module.exports = createJestConfig(customJestConfig);
