const report = require("multiple-cucumber-html-reporter");

report.generate({
  jsonDir: "./cypress/cucumber-json",
  reportPath: "./reports/cucumber-html-report.html",
  metadata: {
    browser: {
      name: process.env.BROWSER_NAME,
      version: process.env.BROWSER_VERSION,
    },
    device: process.env.DEVICE_NAME,
    platform: {
      name: process.env.PLATFORM_NAME,
      version: process.env.PLATFORM_VERSION,
    },
  },
  customData: {
    title: "Run info",
    data: [
      { label: "Project", value: "Zango e2e-Tests Report" },
      { label: "Release", value: "Phase 1" },
      { label: "Cycle", value: "A1" },
      { label: "Execution Date Time", value: new Date().toISOString() },
    ],
  },
});
