module.exports = {
  preset: '@vue/cli-plugin-unit-jest',
  transformIgnorePatterns: [
    '/node_modules/(?!axios)/', // Whitelist axios to be transformed
  ],
  // If you encounter issues with other ES modules in node_modules, add them here too, e.g.:
  // '/node_modules/(?!axios|other-module|another-module)/',
};
