import { Given, When, Then, And } from "cypress-cucumber-preprocessor/steps";
import appPanelPageObjects from "../../support/pageObjectModel/appPanelPageObjects";
let appData = "";
const file_path = "logo.png"; //file name
const time_zone = "Africa/Accra";
const date_format = "04 October 2017";
const date_time_format = "04 October 2017 01:48 PM";
Given("Admin logins successfully and lands on the details view of App", () => {
  cy.login("platform_admin@zango.dev", "Zango@123");
  cy.fixture("appData").then(function (data) {
    appData = data;
    cy.log(appData);
    cy.intercept("GET", `/api/v1/apps/${appData.app_uuid}/*`).as(
      "getAppConfigTab"
    );
    appPanelPageObjects.getAppName().contains(appData.app_name).click();
    appPanelPageObjects.getMenuList().contains("App Settings").click();
    appPanelPageObjects.getAppConfigurationTab().click();
  });
});

When("Validate the app configuration URL", () => {
  cy.url().should("contain", "/app-settings/app-configuration/");
  cy.log("Validated URL");
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
  "Api response post landing on the app configuration should have same app name and app uuid",
  () => {
    cy.wait("@getAppConfigTab").then((intercept) => {
      // Assert on the API response
      expect(JSON.parse(intercept.response.body).response.app.name).to.equal(
        appData.app_name
      );
      expect(JSON.parse(intercept.response.body).response.app.uuid).to.equal(
        appData.app_uuid
      );
    });
  }
);

When(
  "Admin clicks on the update details button in the app details view",
  () => {
    appPanelPageObjects.getUpdateDetails().click();
    cy.wait(2000);
  }
);

And(
  "App update form should be displayed with the following fields",
  (datatables) => {
    datatables.hashes().forEach((element) => {
      appPanelPageObjects
        .getTextField()
        .children()
        .should("have.text", element.field_name_1);
      appPanelPageObjects
        .getTextArea()
        .children()
        .should("contain", element.field_name_2);
      appPanelPageObjects
        .getLogoUploadButton()
        .siblings()
        .should("contain", element.field_name_3);
      appPanelPageObjects
        .getFavIconButton()
        .siblings()
        .should("contain", element.field_name_4);
      appPanelPageObjects.getDomain().should("have.text", element.field_name_5);
      appPanelPageObjects
        .getTimeZone()
        .parents()
        .should("contain", element.field_name_6);
      appPanelPageObjects
        .getDateFormat()
        .parents()
        .should("contain", element.field_name_7);
      appPanelPageObjects
        .getDateTimeFormat()
        .parents()
        .should("contain", element.field_name_8);
    });
  }
);
And(
  "Admin fills the app details form with the valid data and submits the form",
  () => {
    cy.intercept("PUT", `/api/v1/apps/${appData.app_uuid}/`).as("getAppUpdate");
    appPanelPageObjects.getUpdateDetails().click({ force: true });
    appPanelPageObjects.getLogoUploadButton().attachFile(file_path);
    appPanelPageObjects.getFavIconButton().attachFile(file_path);
    // Attach the file to the file input element
    appPanelPageObjects.getAddDomainButton().click({ force: true });
    appPanelPageObjects.getEnterDomainURl().type(appData.domain_url);
    appPanelPageObjects.getTimeZone().click({ force: true });
    appPanelPageObjects
      .getDropDownValues()
      .contains(time_zone)
      .click({ force: true });
    appPanelPageObjects.getDateFormat().click({ force: true });
    appPanelPageObjects
      .getDropDownValues()
      .contains(date_format)
      .click({ force: true });
    appPanelPageObjects.getDateTimeFormat().click({ force: true });
    appPanelPageObjects
      .getDropDownValues()
      .contains(date_time_format)
      .click({ force: true });
    appPanelPageObjects.getUpdateSubmitButton().click({ force: true });
  }
);

Then(
  "App details should be successfully updated and also the Api response should have message {string} and status code {int}",
  (message, statusCode) => {
    cy.wait("@getAppUpdate").then((intercept) => {
      expect(intercept.response.statusCode).to.eq(statusCode);
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
    });
  }
);

When("Admin lands back on the details view", () => {
  cy.url().should("contain", "/app-settings/app-configuration/");
});

Then("App details should be updated as expected", () => {
  appPanelPageObjects
    .getFirstRowValue()
    .should("contain", "App Description")
    .siblings()
    .should("contain", appData.app_description);
  appPanelPageObjects
    .getSecondRowValue()
    .should("contain", "Logo")
    .siblings()
    .should("exist");
  appPanelPageObjects
    .getThirdRowValue()
    .should("contain", "Fav Icon")
    .siblings()
    .should("exist");
  appPanelPageObjects
    .getFourthRowValue()
    .should("contain", "Domain")
    .siblings()
    .should("have.text", appData.domain_url);
  appPanelPageObjects
    .getFifthRowValue()
    .should("contain", "Timezone")
    .siblings()
    .should("have.text", time_zone);
  appPanelPageObjects
    .getSixthRowValue()
    .should("contain", "Date-Time Format")
    .siblings()
    .should("have.text", date_time_format);
  appPanelPageObjects
    .getSeventhRowValue()
    .should("contain", "Date Format")
    .siblings()
    .should("have.text", date_format);
});
