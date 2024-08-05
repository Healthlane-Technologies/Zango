import appPanelPageObjects from "../../support/pageObjectModel/appPanelPageObjects";
let appData = "";

Given(
  "Admin logins successfully and lands on the home page of App panel",
  () => {
    cy.login("platform_admin@zango.dev", "Zango@123");
    const dynamicData = {
      app_name: `app_${Math.floor(Math.random() * 10000)}`, //To create random text
      app_description: `app_${Math.floor(Math.random() * 10000)}`, //To create random text
      domain_url: `https://test${Math.floor(Math.random() * 10000)}.com`,
      // Add more fields as needed
    };
    // Write the dynamic data to a file in the fixtures folder
    cy.writeFile("cypress/fixtures/appData.json", dynamicData).then(() => {
      // Success message after writing the data
      cy.log("Dynamic data is created and stored in the fixtures folder.");
    });
    cy.readFile("cypress/fixtures/appData.json");
    expect(Cypress.currentRetry).to.eq(0);
    cy.fixture("appData").then(function (data) {
      appData = data;
      cy.log(appData);
    });
  }
);

When("Admin clicks on the app launch button on homepage", () => {
  appPanelPageObjects
    .getAppLaunchButton()
    .should("contain", "Launch New App")
    .click();
});

And(
  "Admin fills the app launch form with the valid data and submits the form",
  () => {
    cy.intercept("POST", "/api/v1/apps/").as("getAppData");
    appPanelPageObjects.getTextField().type(appData.app_name);
    appPanelPageObjects.getTextArea().type(appData.app_description);
    appPanelPageObjects.getSubmitButton().click();
    cy.wait(5000);
    cy.log("App Launched");
  }
);

Then(
  "App should be successfully Launched and also the Api response should have message {string} and status code {int}",
  (message, statusCode) => {
    cy.wait("@getAppData").then((intercept) => {
      expect(intercept.response.statusCode).to.eq(statusCode);
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
      const responseBody = JSON.parse(intercept.response.body);
      let uuid = responseBody.response.app_uuid;
      cy.log("app_uuid=" + uuid);
      cy.readFile("cypress/fixtures/appData.json").then((data) => {
        cy.log("running....");
        cy.writeFile("cypress/fixtures/appData.json", {
          ...data,
          app_uuid: uuid,
        });
      });
    });
  }
);
