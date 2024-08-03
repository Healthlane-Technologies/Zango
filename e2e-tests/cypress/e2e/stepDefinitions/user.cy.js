import { Given, When, Then, And } from "cypress-cucumber-preprocessor/steps";
import appPanelPageObjects from "../../support/pageObjectModel/appPanelPageObjects";
import { error_message } from "../../e2e/utils/helper";
let userData;
let appData;
let userRole;

Given(
  "Admin navigates to the user tab and gets the user data from fixture data",
  () => {
    cy.login("platform_admin@zango.dev", "Zango@123");
    cy.fixture("userRoleData").then(function (data) {
      userRole = data;
    });
    cy.fixture("appData").then(function (data) {
      appData = data;
      cy.log(appData);
      cy.intercept("GET", `/api/v1/apps/${appData.app_uuid}/users/*`).as(
        "getUserTab"
      );
      appPanelPageObjects.getAppName().contains(appData.app_name).click();
      appPanelPageObjects.getuserTab().click();
      cy.wait(2000);
    });
  }
);
When("Admin clicks on the new user button on the user page", () => {
  const add_user = '[data-cy="add_user_button"]';
  const new_user = '[data-cy="new_user_button"]';
  cy.multipleLocator(add_user, new_user);
});
And("Admin creates the dynamic data of the user creation", () => {
  const dynamicData = {
    user_name: `user_${Math.floor(Math.random() * 10000)}`,
    updated_user_name: `user_${Math.floor(Math.random() * 10000)}`, //To create random text
    user_email: `user_${Math.floor(Math.random() * 10000)}@example.com`,
    updated_user_email: `user_${Math.floor(Math.random() * 10000)}@example.com`, //To generate email ID's
    user_mobile_number_indian: `9${
      Math.floor(Math.random() * 800000000) + 100000000
    }`, // Random indian mobile number
    updated_user_mobile_number_indian: `9${
      Math.floor(Math.random() * 800000000) + 100000000
    }`,
    // mobile_number_thailand: `+662${Math.floor(Math.random() * 10000000)}`, // Random thailand mobile number
    // mobile_number_malaysia: `+6003${Math.floor(Math.random() * 10000000)}`, // Random malaysia/singapore mobile number
    user_password: `Test@123`, //To create static text
    // Add more fields as needed
  };
  // Write the dynamic data to a file in the fixtures folder
  cy.writeFile("cypress/fixtures/userData.json", dynamicData).then(() => {
    // Success message after writing the data
    cy.log("Dynamic data is created and stored in the fixtures folder.");
  });
  cy.readFile("cypress/fixtures/userData.json");
  expect(Cypress.currentRetry).to.eq(0);
  cy.fixture("userData").then(function (data) {
    userData = data;
    cy.log(userData);
  });
});
And("Add user form is dispalyed with the following fields", (datatables) => {
  datatables.hashes().forEach((element) => {
    appPanelPageObjects
      .getUserFullName()
      .children()
      .should("have.text", element.field_name_1);
    appPanelPageObjects
      .getUserEmail()
      .children()
      .should("have.text", element.field_name_2);
    appPanelPageObjects
      .getUserMobileNumber()
      .children()
      .should("contain", element.field_name_3);
    appPanelPageObjects
      .getUserPassword()
      .children()
      .should("have.text", element.field_name_4);
    appPanelPageObjects
      .getUserRoles()
      .siblings()
      .should("have.text", element.field_name_5);
  });
});
And("Admin fills up the user form with valid data and submits the form", () => {
  cy.intercept("POST", `/api/v1/apps/${appData.app_uuid}/users/`).as(
    "userCreation"
  );
  appPanelPageObjects.getUserFullName().type(userData.user_name);
  appPanelPageObjects.getUserEmail().type(userData.user_email);
  appPanelPageObjects
    .getUserMobileNumber()
    .type(userData.user_mobile_number_indian);
  appPanelPageObjects.getUserPassword().type(userData.user_password);
  appPanelPageObjects.getUserRoles().click();
  appPanelPageObjects
    .getUserDropdown()
    .focus()
    .contains(userRole.updated_user_role)
    .click({ force: true });
  appPanelPageObjects.getSubmitButton().click({ force: true });
});
Then(
  "User should be successfully addded and admin should be redirected to the table view",
  () => {
    cy.url().should("contain", "/user-management");
  }
);
And("Validate the user tab URL", () => {
  cy.url().should("contain", "/user-management");
});
And("User table should contain the following columns", (datatables) => {
  datatables.hashes().forEach((element) => {
    appPanelPageObjects
      .getUserColumnOneHeader()
      .should("contain", element.Column_1)
      .next()
      .should("contain", element.Column_2)
      .next()
      .should("contain", element.Column_3)
      .next()
      .should("contain", element.Column_4)
      .next()
      .should("contain", element.Column_5)
      .next()
      .should("contain", element.Column_6)
      .next()
      .should("contain", element.Column_7);
  });
});
And(
  "Admin clicks on the user table search button and Enters the valid data",
  () => {
    cy.fixture("userData").then(function (data) {
      userData = data;
      appPanelPageObjects.getUserSearchBar().type(userData.user_name);
    });
    cy.intercept("GET", `/api/v1/apps/${appData.app_uuid}/users/*`).as(
      "getUser"
    );
    cy.wait(2000);
  }
);
Then("User table row should contain the valid data", () => {
  appPanelPageObjects
    .getFirstRowValue()
    .invoke("text")
    .then((text) => {
      cy.log(text);
      appPanelPageObjects
        .getUserTableValue()
        .should("contain", userData.user_name)
        .next()
        .should("contain", userData.user_mobile_number_indian)
        .next()
        .should("contain", userData.user_email)
        .next()
        .should("contain", userRole.updated_user_role);
    });
});
And("Admin skips the mandatory fields on user form", () => {
  appPanelPageObjects.getUserFullName().click();
  appPanelPageObjects.getUserEmail().click();
  appPanelPageObjects.getUserMobileNumber().click();
  appPanelPageObjects.getUserPassword().click();
  appPanelPageObjects.getUserRoles().click();
  appPanelPageObjects.getSubmitButton().click({ force: true });
});
Then("Required field error message for user from should be displayed", () => {
  appPanelPageObjects.getUserFullName().then(($error) => {
    error_message();
  });
  appPanelPageObjects.getUserEmail().then(() => {
    error_message();
  });
  appPanelPageObjects.getUserMobileNumber().then(() => {
    error_message();
  });
  appPanelPageObjects.getUserPassword().then(() => {
    error_message();
  });
  appPanelPageObjects.getUserRoles().then(() => {
    error_message();
  });
});
Then("Error message for duplication of user should be displayed", () => {
  appPanelPageObjects
    .getErrorMessage()
    .should(
      "contain",
      "Another user already exists matching the provided credentials"
    );
  appPanelPageObjects.getGoBackButton().click();
});
And("Admin also wants to assert the Api response post user addition", () => {
  cy.url().should("contain", "/user-management/");
});
Then(
  "Api response post landing on user tab should have message {string} and status code {int}",
  (message, status_code) => {
    cy.wait("@getUserTab").then((intercept) => {
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
      expect(intercept.response.statusCode).to.eq(status_code);
    });
  }
);
Then(
  "Api response post user creation should have message {string} and status code {int}",
  (message, status_code) => {
    cy.wait("@userCreation").then((intercept) => {
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
      expect(intercept.response.statusCode).to.eq(status_code);
    });
  }
);
Then(
  "Api response post search should have message {string} total records should be {int} and status code {int} in user table",
  (message, total_records, status_code) => {
    cy.wait("@getUser").then((intercept) => {
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
      expect(intercept.response.statusCode).to.eq(status_code);
      expect(
        JSON.parse(intercept.response.body).response.users.total_records
      ).to.equal(total_records);

      const responseBody = JSON.parse(intercept.response.body);
      let userID_fetched = responseBody.response.users.records[0].id;
      cy.log("fetched_userID=" + userID_fetched);
    });
  }
);

And(
  "Admin clicks on the deactivate user button under the three dots menu",
  () => {
    cy.wait("@getUser").then((intercept) => {
      const responseBody = JSON.parse(intercept.response.body);
      let userID_fetched = responseBody.response.users.records[0].id;
      cy.log("userID_fetched=" + userID_fetched);
      cy.intercept("PUT", `/api/v1/apps/${appData.app_uuid}/users/*`).as(
        "userUpdate"
      );
      cy.wait(3000);
      cy.get("table > tbody > tr").trigger("mouseover");
      appPanelPageObjects.getThreeDotsMenu().click({
        force: true,
        multiple: true,
      });
      appPanelPageObjects.getDeactivateUserButton().click({
        force: true,
        multiple: true,
      });
      appPanelPageObjects.getSubmitButton().click({ force: true });
    });
  }
);
And(
  "Admin clicks on the activate user button under the three dots menu",
  () => {
    cy.wait("@getUser").then((intercept) => {
      const responseBody = JSON.parse(intercept.response.body);
      let userID_fetched = responseBody.response.users.records[0].id;
      cy.log("userID_fetched=" + userID_fetched);
      cy.intercept("PUT", `/api/v1/apps/${appData.app_uuid}/users/*`).as(
        "userUpdate"
      );
      cy.wait(3000);
      cy.get("table > tbody > tr").trigger("mouseover");
      appPanelPageObjects.getThreeDotsMenu().click({
        force: true,
        multiple: true,
      });
      appPanelPageObjects.getActivateUserButton().click({
        force: true,
        multiple: true,
      });
      appPanelPageObjects.getSubmitButton().click({ force: true });
    });
  }
);
And(
  "Api response post update should have message {string} and status code {int}",
  (message, status_code) => {
    cy.wait("@userUpdate").then((intercept) => {
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
      expect(intercept.response.statusCode).to.equal(status_code);
    });
  }
);
And("Post deactivation user should get deactivated", () => {
  cy.wait("@getUser").then((intercept) => {
    expect(
      JSON.parse(intercept.response.body).response.users.records[0].is_active
    ).to.equal(false);
  });
});
And("Post activation user should get activated", () => {
  cy.wait("@getUser").then((intercept) => {
    expect(
      JSON.parse(intercept.response.body).response.users.records[0].is_active
    ).to.equal(true);
  });
});
And("Admin clicks on the edit user button under the three dots menu", () => {
  cy.wait("@getUser").then((intercept) => {
    const responseBody = JSON.parse(intercept.response.body);
    let userID_fetched = responseBody.response.users.records[0].id;
    cy.log("userID_fetched=" + userID_fetched);
    cy.intercept("PUT", `/api/v1/apps/${appData.app_uuid}/users/*`).as(
      "userUpdate"
    );
    cy.wait(3000);
    appPanelPageObjects.getThreeDotsMenu().click({
      force: true,
      multiple: true,
    });
    cy.get('[data-cy="edit_user_details_button"]').click({
      force: true,
      multiple: true,
    });
    cy.wait(2000);
  });
});
And("Admin updates the user form with the valid data", () => {
  cy.wait("@getUser").then((intercept) => {
    // Assert on the API response
    const responseBody = JSON.parse(intercept.response.body);
    let user_id = responseBody.response.roles.records[0].id;
    cy.log("user_id=" + user_id);
    cy.intercept("PUT", `/api/v1/apps/${appData.app_uuid}/roles/${user_id}`).as(
      "userRoleUpdate"
    );
    appPanelPageObjects
      .getUserFullName()
      .clear()
      .type(userData.user_name)
      .then(($button) => {
        expect($button).to.not.have.attr("disabled");
      });
  });
});
