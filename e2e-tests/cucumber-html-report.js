const report = require("multiple-cucumber-html-reporter");

report.generate({
  jsonDir: "e2e-tests/cypress/cucumber-json",
  reportPath: "./reports",
  metadata: {
    browser: {
      name: "chrome",
      version: "126",
    },
    device: "MacBook Air",
    platform: {
      name: "Mac OS",
      version: "Sonoma 14.2",
    },
  },
  customData: {
    title: "Run info",
    data: [
      { label: "Project", value: "Zango e2e Tests" },
      { label: "Release", value: "Phase 1" },
      { label: "Cycle", value: "A1" },
      { label: "Execution Start Time", value: new Date().getTime() },
      { label: "Execution End Time", value: new Date().getTime() },
    ],
  },
});
