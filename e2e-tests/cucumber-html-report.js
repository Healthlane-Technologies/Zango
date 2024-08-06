const report = require("multiple-cucumber-html-reporter");

const executionDateTime = new Date().toLocaleString("en-US", {
  timeZone: "Asia/Kolkata",
  year: "numeric",
  month: "long",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: true,
});

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
      { label: "Zango Version", value: process.env.ZANGO_VERSION },
      { label: "Execution Date Time", value: executionDateTime },
      { label: "Execution Environment", value: process.env.CI_ENVIRONMENT },
      { label: "Execution Duration", value: process.env.DURATION },
    ],
  },
});
