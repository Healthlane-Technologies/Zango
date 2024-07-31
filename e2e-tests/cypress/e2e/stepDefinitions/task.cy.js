import { Given, When, Then, And } from "cypress-cucumber-preprocessor/steps";
import appPanelPageObjects from "../../support/pageObjectModel/appPanelPageObjects";
let appData = "";

Given("User navigates to task tab", () => {
  cy.login("platform_admin@zango.dev", "Zango@123");
  cy.fixture("appData").then(function (data) {
    appData = data;
    cy.log(appData);
    cy.intercept("GET", `/api/v1/apps/${appData.app_uuid}/tasks/*`).as(
      "getTaskTab"
    );
    appPanelPageObjects.getAppName().contains(appData.app_name).click();
    appPanelPageObjects.getTasksTab().click();
  });
});

When("Validate the task tab URL", () => {
  cy.url().should("contain", "/tasks-management");
});

And("Task table should contain the following columns", (datatables) => {
  datatables.hashes().forEach((element) => {
    appPanelPageObjects
      .getTableColumnOneHeader()
      .should("contain", element.Column_1)
      .next()
      .should("contain", element.Column_2)
      .next()
      .should("contain", element.Column_3)
      .next()
      .should("contain", element.Column_4)
      .next()
      .should("contain", element.Column_5);
  });
});

Then(
  "Api response post landing on tasks tab should have message {string} and status code {int}",
  (message, status_code) => {
    cy.wait("@getTaskTab").then((intercept) => {
      // Assert on the API response
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
      expect(intercept.response.statusCode).to.eq(status_code);
    });
  }
);

When("Admin clicks on the sync task button", () => {
  cy.intercept("POST", `/api/v1/apps/${appData.app_uuid}/tasks/*`).as(
    "getSyncTasks"
  );
  appPanelPageObjects.getSyncTaskButton().click();
  cy.wait(2000);
});

Then(
  "Api response post syncing tasks should have message {string} and status code {int}",
  (message, statusCode) => {
    cy.wait("@getSyncTasks").then((intercept) => {
      expect(intercept.response.statusCode).to.eq(statusCode);
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
    });
  }
);
