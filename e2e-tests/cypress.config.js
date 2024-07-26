const cucumber = require("cypress-cucumber-preprocessor").default;

const { defineConfig } = require("cypress");

module.exports = defineConfig({
  projectId: "49hfyd",
  chromeWebSecurity: false,
  reporterOptions: {
    reportDir: "cypress/reports",
    charts: true,
    reportPageTitle: "Zango",
    embeddedScreenshots: true,
  },
  e2e: {
    experimentalRunAllSpecs: true,
    setupNodeEvents(on, config) {
      on("file:preprocessor", cucumber());
    },
    // specPattern: "**/*.feature",
    specPattern: "cypress/e2e/**/*.feature",
    // specPattern: "cypress/e2e/**/*.cy.{js,jsx,ts,tsx}",
  },
});
