import { Given, When, Then, And } from "cypress-cucumber-preprocessor/steps";
import appPanelPageObjects from "../../support/pageObjectModel/appPanelPageObjects";
import { error_message } from "../../e2e/utils/helper";
let platformUserData;
let appData;
Given(
  "Admin navigates to the user management tab and gets the platform user data from fixtures",
  () => {
    // cy.login("platform_admin@zelthy.com", "Zelthy@123");
    cy.login("platform_admin@zango.dev", "Zango@123");
    cy.intercept("GET", "api/v1/auth/platform-users/*").as("getPlatformUser");
    appPanelPageObjects.getTopMenuButton().click();
    appPanelPageObjects.getTopMenuItems().contains("User Management").click();
    cy.fixture("appData").then(function (data) {
      appData = data;
    });
  }
);
When("Admin clicks on the new user button on the user management page", () => {
  appPanelPageObjects.getAddUserManagement().click();
});
And("Admin creates the dynamic data of the platform user", () => {
  const dynamicData = {
    platform_user_name: `user_${Math.floor(Math.random() * 10000)}`, //To create random text
    updated_platform_user_name: `updated_user_${Math.floor(
      Math.random() * 10000
    )}`,
    platform_user_email: `user_${Math.floor(
      Math.random() * 10000
    )}@example.com`, //To generate email ID's
    platform_user_password: `Test@123`, //To create static text
    // Add more fields as needed
    platform_user_reset_password: `Zelthy@123`,
  };
  // Write the dynamic data to a file in the fixtures folder
  cy.writeFile("cypress/fixtures/platformUserData.json", dynamicData).then(
    () => {
      // Success message after writing the data
      cy.log("Dynamic data is created and stored in the fixtures folder.");
    }
  );
  cy.readFile("cypress/fixtures/platformUserData.json").then(() => {
    expect(Cypress.currentRetry).to.eq(0);
  });
  cy.fixture("platformUserData").then(function (data) {
    platformUserData = data;
  });
});
And(
  "Add platform user form is dispalyed with the following fields",
  (datatables) => {
    datatables.hashes().forEach((element) => {
      appPanelPageObjects
        .getUserManagementFullName()
        .parent()
        .should("have.text", element.field_name_1);
      appPanelPageObjects
        .getUserManagementEmail()
        .parent()
        .should("have.text", element.field_name_2);
      appPanelPageObjects
        .getUserManagementPassword()
        .parent()
        .should("have.text", element.field_name_3);
      appPanelPageObjects
        .getUserManagementAppsAccess()
        .parent()
        .should("contain", element.field_name_4);
    });
  }
);
And(
  "Admin fills up the platform user form with valid data and submits the form",
  () => {
    cy.intercept("POST", `/api/v1/auth/platform-users/`).as(
      "platformUserCreation"
    );
    appPanelPageObjects
      .getUserManagementFullName()
      .type(platformUserData.platform_user_name);
    appPanelPageObjects
      .getUserManagementEmail()
      .type(platformUserData.platform_user_email);
    appPanelPageObjects
      .getUserManagementPassword()
      .type(platformUserData.platform_user_password);
    appPanelPageObjects.getUserManagementAppsAccess().click();
    appPanelPageObjects
      .getUserManagementDropdownValues()
      .contains(appData.app_name)
      .click({ force: true });
    appPanelPageObjects.getSubmitButton().click({ force: true });
  }
);
Then(
  "Platform User should be successfully added and admin should be redirected to the table view",
  () => {
    cy.url().should("contain", "/user-managements");
  }
);
And(
  "Admin also wants to assert the Api response post platform user creation",
  () => {
    cy.url().should("contain", "/user-managements");
  }
);
Then(
  "Api response post platform user creation should have message {string} and status code {int}",
  (message, status_code) => {
    cy.wait("@platformUserCreation").then((intercept) => {
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
      expect(intercept.response.statusCode).to.eq(status_code);
    });
  }
);
And("Admin skips the mandatory fields on the platform user form", () => {
  appPanelPageObjects.getUserManagementFullName().click();
  appPanelPageObjects.getUserManagementEmail().click();
  appPanelPageObjects.getUserManagementPassword().click();
  appPanelPageObjects.getUserManagementAppsAccess().click();
});

Then(
  "Required field error message should be displayed on the platform user form",
  () => {
    appPanelPageObjects.getUserManagementFullName().then(($error) => {
      error_message();
    });
    appPanelPageObjects.getUserManagementEmail().then(($error) => {
      error_message();
    });
    appPanelPageObjects.getUserManagementPassword().then(($error) => {
      error_message();
    });
    appPanelPageObjects.getUserManagementAppsAccess().then(($error) => {
      appPanelPageObjects
        .getErrorMessage()
        .should("contain", "Minimun one is required");
    });
  }
);
Then(
  "Error message for duplication of platform user management should be displayed",
  () => {
    appPanelPageObjects
      .getErrorMessage()
      .should(
        "contain",
        "Another user already exists matching the provided credentials"
      );
    appPanelPageObjects.getGoBackButton().click();
  }
);
When("Admin wants to validate the user management tab URL", () => {
  cy.url().should("contain", "/user-managements");
});
And(
  "User management table should contain the following columns",
  (datatables) => {
    datatables.hashes().forEach((element) => {
      appPanelPageObjects
        .getUserManagementColumnHeader()
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
  }
);
And(
  "Admin clicks on the user management table search button and Enters the valid data",
  () => {
    cy.fixture("platformUserData").then(function (data) {
      platformUserData = data;
      appPanelPageObjects
        .getUserManagementSearchBar()
        .type(platformUserData.platform_user_name);
    });
    cy.intercept("GET", "/api/v1/auth/platform-users/*").as(
      "getPlatformUserSearch"
    );
  }
);
Then("User management table row should contain the valid data", () => {
  appPanelPageObjects
    .getFirstRowValue()
    .invoke("text")
    .then((text) => {
      cy.log(text);
      cy.readFile("cypress/fixtures/platformUserData.json").then((data) => {
        cy.log("running....");
        cy.writeFile("cypress/fixtures/platformUserData.json", {
          ...data,
          platform_userID: text,
        });
      });
      appPanelPageObjects
        .getUserManagementTableValue()
        .should("contain", platformUserData.platform_user_name)
        .next()
        .should("contain", platformUserData.platform_user_email)
        .next()
        .should("contain", appData.app_name);
    });
});
When("Admin lands on the user management tab", () => {
  cy.url().should("contain", "/user-managements");
});
Then(
  "Api response post landing on user management tab should have message {string} and status code {int}",
  (message, status_code) => {
    cy.wait("@getPlatformUser").then((intercept) => {
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
      expect(intercept.response.statusCode).to.eq(status_code);
    });
  }
);
Then(
  "Api response post search should have message {string} total records should be {int} and status code {int} in platform user table",
  (message, total_records, status_code) => {
    cy.wait("@getPlatformUserSearch").then((intercept) => {
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
      expect(intercept.response.statusCode).to.eq(status_code);
      expect(
        JSON.parse(intercept.response.body).response.platform_users
          .total_records
      ).to.equal(total_records);
      const responseBody = JSON.parse(intercept.response.body);
      let platform_userID_fetched =
        responseBody.response.platform_users.records[0].id;
      cy.log("fetched_platformuserID=" + platform_userID_fetched);
    });
  }
);
And(
  "Admin clicks on the deactivate platform user button under the three dots menu",
  () => {
    cy.wait("@getPlatformUserSearch").then((intercept) => {
      const responseBody = JSON.parse(intercept.response.body);
      let platform_userID_fetched =
        responseBody.response.platform_users.records[0].id;
      cy.log("fetched_platformuserID=" + platform_userID_fetched);
      cy.intercept(
        "PUT",
        `/api/v1/auth/platform-users/${platform_userID_fetched}`
      ).as("getPlatformUserUpdate");
      cy.wait(3000);
      cy.get("table > tbody > tr").trigger("mouseover");
      appPanelPageObjects.getThreeDotsMenu().click({
        force: true,
        multiple: true,
      });
      appPanelPageObjects.getDeactivatePlatformUserRoleButton().click({
        force: true,
        multiple: true,
      });
      appPanelPageObjects.getSubmitButton().click({ force: true });
    });
  }
);
And(
  "Admin clicks on the activate platform user button under the three dots menu",
  () => {
    cy.wait("@getPlatformUserSearch").then((intercept) => {
      const responseBody = JSON.parse(intercept.response.body);
      let platform_userID_fetched =
        responseBody.response.platform_users.records[0].id;
      cy.log("fetched_platformuserID=" + platform_userID_fetched);
      cy.intercept(
        "PUT",
        `/api/v1/auth/platform-users/${platform_userID_fetched}`
      ).as("getPlatformUserUpdate");
      cy.wait(3000);
      cy.get("table > tbody > tr").trigger("mouseover");
      appPanelPageObjects.getThreeDotsMenu().click({
        force: true,
        multiple: true,
      });
      appPanelPageObjects.getActivatePlatformUserRoleButton().click({
        force: true,
        multiple: true,
      });
      appPanelPageObjects.getSubmitButton().click({ force: true });
    });
  }
);
And(
  "Api response post platform user update should have message {string} and status code {int}",
  (message, status_code) => {
    cy.wait("@getPlatformUserUpdate").then((intercept) => {
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
      expect(intercept.response.statusCode).to.equal(status_code);
    });
  }
);
Then("Post deactivation platform user should get deactivated", () => {
  cy.wait("@getPlatformUserSearch").then((intercept) => {
    expect(
      JSON.parse(intercept.response.body).response.platform_users.records[0]
        .is_active
    ).to.equal(false);
  });
});
And("Post activation platform user should get activated", () => {
  cy.wait("@getPlatformUserSearch").then((intercept) => {
    expect(
      JSON.parse(intercept.response.body).response.platform_users.records[0]
        .is_active
    ).to.equal(true);
  });
});
And(
  "Admin clicks on the edit platform user button under the three dots menu",
  () => {
    cy.wait("@getPlatformUserSearch").then((intercept) => {
      const responseBody = JSON.parse(intercept.response.body);
      let platform_userID_fetched =
        responseBody.response.platform_users.records[0].id;
      cy.log("fetched_platformuserID=" + platform_userID_fetched);
      cy.intercept(
        "PUT",
        `/api/v1/auth/platform-users/${platform_userID_fetched}`
      ).as("getPlatformUserUpdate");
      cy.wait(3000);
      cy.get("table > tbody > tr").trigger("mouseover");
      appPanelPageObjects.getThreeDotsMenu().click({
        force: true,
        multiple: true,
      });
      appPanelPageObjects.getEditPlatformUserRoleButton().click({
        force: true,
        multiple: true,
      });
      cy.wait(3000);
    });
  }
);
And("Admin updates the platform user form with the valid data", () => {
  appPanelPageObjects
    .getUserManagementFullName()
    .clear()
    .type(platformUserData.updated_platform_user_name)
    .then(($button) => {
      expect($button).to.not.have.attr("disabled");
    });
  appPanelPageObjects.getSubmitButton().click();
});
And(
  "Admin clicks on the reset platform user button under the three dots menu",
  () => {
    cy.wait("@getPlatformUserSearch").then((intercept) => {
      const responseBody = JSON.parse(intercept.response.body);
      let platform_userID_fetched =
        responseBody.response.platform_users.records[0].id;
      cy.log("fetched_platformuserID=" + platform_userID_fetched);
      cy.wait(3000);
      cy.get("table > tbody > tr").trigger("mouseover");
      appPanelPageObjects.getThreeDotsMenu().click({
        force: true,
        multiple: true,
      });
      appPanelPageObjects.getPlatformUserResetPwdButton().click({
        force: true,
        multiple: true,
      });
      cy.wait(3000);
    });
  }
);
And("Admin resets the platform user password with the valid data", () => {
  cy.intercept("PUT", `/api/v1/auth/platform-users/*`).as(
    "getPlatformUserUpdate"
  );
  appPanelPageObjects
    .getPlatformUserResetPwdField()
    .type(platformUserData.platform_user_reset_password)
    .then(($button) => {
      expect($button).to.not.have.attr("disabled");
    });
  appPanelPageObjects.getSubmitButton().click();
});
Given("Platform user navigates to the application URL", () => {
  cy.visit("http://localhost:8000/auth/login/?next=/platform/");
  cy.fixture("appData").then(function (data) {
    appData = data;
  });
  cy.fixture("platformUserData").then(function (data) {
    platformUserData = data;
  });
});
When("Platform user validates the application URL", () => {
  cy.url().should("contain", "/auth/login/");
});
And(
  "Platform user login form is dispalyed with the following fields",
  (datatables) => {
    datatables.hashes().forEach((element) => {
      appPanelPageObjects
        .getPlatformUsername()
        .should("have.attr", "placeholder", element.field_name_1);
      appPanelPageObjects
        .getPlatformUserPassword()
        .should("have.attr", "placeholder", element.field_name_2);
    });
  }
);
And(
  "Platform user fills the login form with the valid details and click on the submit button",
  () => {
    cy.intercept("GET", "/api/v1/auth/app-initalization-details/").as(
      "platformUserLogin"
    );
    cy.intercept("GET", "/api/v1/apps/").as("platformUserApps");
    appPanelPageObjects
      .getPlatformUsername()
      .type(platformUserData.platform_user_email);
    appPanelPageObjects
      .getPlatformUserPassword()
      .type(platformUserData.platform_user_reset_password);
    appPanelPageObjects.getPlatformLoginButton().click();
    cy.wait(3000);
  }
);
Then(
  "Platform user should be successfully logged in and should be redirected to the application platform",
  () => {
    cy.url().should("contain", "/platform/apps");
  }
);
Then(
  "Post logging into the application platform user should be activated",
  () => {
    cy.wait("@platformUserLogin").then((intercept) => {
      const responseBody = JSON.parse(intercept.response.body);
      expect(responseBody.response.app_data.user_logged_in.is_active).to.equal(
        true
      );
      expect(
        responseBody.response.app_data.user_logged_in.is_superadmin
      ).to.equal(false);
      expect(responseBody.response.app_data.user_logged_in.email).to.equal(
        platformUserData.platform_user_email
      );
      expect(responseBody.response.app_data.user_logged_in.name).to.equal(
        platformUserData.updated_platform_user_name
      );
      expect(
        responseBody.response.app_data.user_logged_in.apps[0].name
      ).to.equal(appData.app_name);
      expect(
        responseBody.response.app_data.user_logged_in.apps[0].uuid
      ).to.equal(appData.app_uuid);
    });
  }
);
Then(
  "Api response post landing on application platform should have message {string} and status code {int}",
  (message, status_code) => {
    cy.wait("@platformUserApps").then((intercept) => {
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
      expect(intercept.response.statusCode).to.eq(status_code);
    });
  }
);
