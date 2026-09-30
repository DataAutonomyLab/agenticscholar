module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Find the rule that handles JavaScript/TypeScript files
      const scope = webpackConfig.module.rules.find(
        (rule) => rule.oneOf
      );

      if (scope) {
        // Find the babel-loader rule within the 'oneOf' array
        const babelLoaderRule = scope.oneOf.find(
          (rule) => rule.loader && rule.loader.includes('babel-loader')
        );

        if (babelLoaderRule) {
          // By default, CRA excludes node_modules from babel-loader.
          // We are modifying the 'exclude' rule to still exclude most of node_modules,
          // but to *include* the 'marked' package so Babel can process it.
          babelLoaderRule.exclude = /node_modules(?!\/marked)/;
        }
      }
      return webpackConfig;
    },
  },
};