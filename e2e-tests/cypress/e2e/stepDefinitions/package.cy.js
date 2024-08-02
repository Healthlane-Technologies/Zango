import { Given, When, Then, And } from "cypress-cucumber-preprocessor/steps";
import appPanelPageObjects from "../../support/pageObjectModel/appPanelPageObjects";
let appData = "";

Given("User navigates to Package tab", () => {
  cy.login("platform_admin@zango.dev", "Zango@123");
  cy.fixture("appData").then(function (data) {
    appData = data;
    cy.log(appData);
    cy.intercept("GET", `/api/v1/apps/${appData.app_uuid}/packages/*`).as(
      "getPackageTab"
    );
    appPanelPageObjects.getAppName().contains(appData.app_name).click();
    appPanelPageObjects.getPackagesTab().click();
  });
});

When("Validate the Package tab URL", () => {
  cy.url().should("contain", "/packages-management");
});

And("Package table should contain the following columns", (datatables) => {
  datatables.hashes().forEach((element) => {
    appPanelPageObjects
      .getTableColumnOneHeader()
      .should("contain", element.Column_1)
      .next()
      .should("contain", element.Column_2)
      .next()
      .should("contain", element.Column_3)
      .next()
      .should("contain", element.Column_4);
  });
});

Then(
  "Api response post landing on Package tab should have status code {int}",
  (status_code) => {
    cy.wait("@getPackageTab").then((intercept) => {
      // Assert on the API response
      expect(intercept.response.statusCode).to.eq(status_code);
    });
  }
);

When("Admin clicks on the sync policy button", () => {
  cy.intercept("POST", `/api/v1/apps/${appData.app_uuid}/policies/*`).as(
    "getSyncPolicies"
  );
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

And(
  "Admin clicks on the package table search button and Enters the {string}",
  (package_name) => {
    appPanelPageObjects.getPackageSearchBar().type(package_name);
    cy.intercept("GET", `/api/v1/apps/${appData.app_uuid}/packages/*`).as(
      "getPackage"
    );
    cy.wait(5000);
  }
);

And(
  "Admin clicks on the install package button under the three dots menu",
  () => {
    cy.wait(5000);
    cy.get("table > tbody > tr:nth-child(1)").trigger("mouseover");
    cy.get('[data-cy="three_dots_menu"]').click({
      force: true,
      multiple: true,
    });
    cy.get('[data-cy="install_package"]').click({
      force: true,
      multiple: true,
    });
  }
);

And("Install package form should contain following fields", (datatables) => {
  datatables.hashes().forEach((element) => {
    appPanelPageObjects
      .getTextField()
      .children()
      .should("have.text", element.field_name_1);
    appPanelPageObjects
      .getDropDownButton()
      .parents()
      .should("contain", element.field_name_2);
  });
});

And("Admin selects the version and submits the form", () => {
  appPanelPageObjects.getDropDownButton().click();
  appPanelPageObjects.getVersion().click();
  // appPanelPageObjects.getSubmitButton().click();
});
