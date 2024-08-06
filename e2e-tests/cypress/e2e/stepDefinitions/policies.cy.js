import { Given, When, Then, And } from "cypress-cucumber-preprocessor/steps";
import appPanelPageObjects from "../../support/pageObjectModel/appPanelPageObjects";
let appData = "";

Given("User navigates to policies tab", () => {
  cy.login("platform_admin@zango.dev", "Zango@123");
  cy.fixture("appData").then(function (data) {
    appData = data;
    cy.log(appData);
    cy.intercept("GET", `/api/v1/apps/${appData.app_uuid}/policies/*`).as(
      "getPoliciesTab"
    );
    appPanelPageObjects.getAppName().contains(appData.app_name).click();
    appPanelPageObjects.getPoliciesTab().click();
    cy.intercept("POST", `/api/v1/apps/${appData.app_uuid}/policies/*`).as(
      "getSyncPolicies"
    );
  });
});

When("Validate the policies tab URL", () => {
  cy.url().should("contain", "/policies");
});

And("Policy table should contain the following columns", (datatables) => {
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
  "Api response post landing on policies tab should have message {string} and status code {int}",
  (message, status_code) => {
    cy.wait("@getPoliciesTab").then((intercept) => {
      // Assert on the API response
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
      expect(intercept.response.statusCode).to.eq(status_code);
    });
  }
);

When("Admin clicks on the sync policy button", () => {
  appPanelPageObjects.getSyncPolicyButton().click();
  cy.wait(2000);
});

Then(
  "Api response post syncing policies should have message {string} and status code {int}",
  (message, statusCode) => {
    cy.wait("@getSyncPolicies").then((intercept) => {
      expect(intercept.response.statusCode).to.eq(statusCode);
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
    });
  }
);
