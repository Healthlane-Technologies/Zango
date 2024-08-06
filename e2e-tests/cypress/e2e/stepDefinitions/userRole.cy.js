import { Given, When, Then, And } from "cypress-cucumber-preprocessor/steps";
import appPanelPageObjects from "../../support/pageObjectModel/appPanelPageObjects";
let userRole = "";
let appData = "";

Given(
  "Admin navigates to the user role tab and gets the user role data from fixture data",
  () => {
    cy.login("platform_admin@zango.dev", "Zango@123");
    cy.fixture("appData").then(function (data) {
      appData = data;
      cy.log(appData);
      cy.intercept("GET", `/api/v1/apps/${appData.app_uuid}/roles/*`).as(
        "getUserRoleTab"
      );
      appPanelPageObjects.getAppName().contains(appData.app_name).click();
      appPanelPageObjects.getuserRolesTab().click();
    });
  }
);

And("Admin creates dynamic data for user role creation", () => {
  const dynamicData = {
    user_role: `app_${Math.floor(Math.random() * 10000)}`, //To create random text
    updated_user_role: `app_${Math.floor(Math.random() * 10000)}`,
    policy_type: `AllowFromAnywhere`,
    // Add more fields as needed
  };
  // Write the dynamic data to a file in the fixtures folder
  cy.writeFile("cypress/fixtures/userRoleData.json", dynamicData).then(() => {
    // Success message after writing the data
    cy.log("Dynamic data is created and stored in the fixtures folder.");
  });
  cy.readFile("cypress/fixtures/userRoleData.json");
  expect(Cypress.currentRetry).to.eq(0);
  cy.fixture("userRoleData").then(function (data) {
    userRole = data;
  });
});

When("Admin clicks on the new user role button on the user role page", () => {
  appPanelPageObjects.getNewUserRole().click({ force: true });
});

And(
  "Add user role form is displayed with the following fields",
  (datatables) => {
    datatables.hashes().forEach((element) => {
      appPanelPageObjects
        .getRoleName()
        .children()
        .should("have.text", element.field_name_1);
      appPanelPageObjects
        .getDropDownButton()
        .siblings()
        .should("have.text", element.field_name_2);
    });
  }
);

And(
  "Admin fills up the user role form with the valid data and submits the form",
  () => {
    cy.intercept("POST", `/api/v1/apps/${appData.app_uuid}/roles/`).as(
      "userRoleCreation"
    );
    appPanelPageObjects
      .getRoleName()
      .clear()
      .type(userRole.user_role)
      .then(($button) => {
        expect($button).to.not.have.attr("disabled");
      });
    appPanelPageObjects.getDropDownButton().click();
    appPanelPageObjects
      .getMultiSelectDropDownValues()
      .contains(userRole.policy_type)
      .click({ force: true })
      .then(() => {
        appPanelPageObjects
          .getDropDownButton()
          .should("have.text", "1 selectedAllowFromAnywhereAllowFromAnywhere");
      });
    appPanelPageObjects.getSubmitButton().click({ force: true });
  }
);

And(
  "Admin fills up the edit user role form with the existing data and submits the form",
  () => {
    appPanelPageObjects
      .getRoleName()
      .clear()
      .type("SystemUsers")
      .then(($button) => {
        expect($button).to.not.have.attr("disabled");
      });
    appPanelPageObjects.getSubmitButton().click({ force: true });
  }
);
And("Admin skips the mandatory fields", () => {
  cy.get('[placeholder="Enter role name"]').click().clear();
  appPanelPageObjects.getSubmitButton().click({ force: true });
});

Then(
  "Required field error message for user role form should be displayed",
  () => {
    appPanelPageObjects.getRoleName().then(($error) => {
      expect($error).to.be.visible;
      appPanelPageObjects.getErrorMessage().should("contain", "Required");
    });
  }
);

Then(
  "User role should be successfully added and admin should be redirected to the table view",
  () => {
    cy.url().should("contain", "/user-roles");
  }
);

Then("Error message for duplication of user role should be displayed", () => {
  appPanelPageObjects
    .getErrorMessage()
    .should(
      "contain",
      "user role model with this Unique Name of the User Role already exists."
    );
  appPanelPageObjects.getGoBackButton().click();
});

When("Validate the user role tab URL", () => {
  cy.url().should("contain", "/user-roles");
});

And("User role table should contain the following columns", (datatables) => {
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

And(
  "Admin clicks on the user role table search button and Enters the valid data",
  () => {
    cy.fixture("userRoleData").then(function (data) {
      userRole = data;
      appPanelPageObjects.getSearchBar().type(userRole.user_role);
    });
    cy.intercept("GET", `/api/v1/apps/${appData.app_uuid}/roles/*`).as(
      "getUserRole"
    );
    cy.wait(5000);
  }
);

Then("User role table row should contain the valid data", () => {
  appPanelPageObjects
    .getFirstRowValue()
    .should("contain", userRole.user_role)
    .next()
    .should("contain", userRole.policy_type)
    .next()
    .should("contain", "Active")
    .next()
    .should("contain", 0);
});

When("User logs into the platform", () => {
  cy.url().should("contain", "/platform/apps");
});

Then(
  "Api response post landing on apps page should have message {string} and status code {int}",
  (message, status_code) => {
    cy.intercept({
      path: "/api/v1/apps/",
    }).as("apps");
    cy.reload();
    cy.wait("@apps").then((intercept) => {
      // Assert on the API response
      expect(intercept.response.statusCode).to.eq(status_code);
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
    });
  }
);

Then(
  "Api response post user role creation should have message {string} and status code {int}",
  (message, status_code) => {
    cy.wait("@userRoleCreation").then((intercept) => {
      // Assert on the API response
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
      expect(intercept.response.statusCode).to.eq(status_code);
      const responseBody = JSON.parse(intercept.response.body);
      let user_id = responseBody.response.role_id;
      cy.log("user_id=" + user_id);
    });
  }
);
And(
  "Admin also wants to assert the Api response post user role addition",
  () => {
    cy.url().should("contain", "/user-roles");
  }
);
Then(
  "Api response post search should have message {string} total records should be {int} and status code {int} in user role table",
  (message, total_records, status_code) => {
    cy.wait("@getUserRole").then((intercept) => {
      // Assert on the API response
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
      expect(intercept.response.statusCode).to.eq(status_code);
      expect(
        JSON.parse(intercept.response.body).response.roles.total_records
      ).to.eq(total_records);
      expect(
        JSON.parse(intercept.response.body).response.roles.records[0].name
      ).to.eq(userRole.user_role);
    });
  }
);

And(
  "Admin clicks on the edit user role button under the three dots menu",
  () => {
    cy.wait(5000);
    cy.get("table > tbody > tr").trigger("mouseover");
    appPanelPageObjects.getThreeDotsMenu().click({
      force: true,
      multiple: true,
    });
    appPanelPageObjects.getEditUserRoleButton().click({
      force: true,
      multiple: true,
    });
  }
);

And(
  "Admin clicks on the deactivate user role button under the three dots menu",
  () => {
    cy.wait("@getUserRole").then((intercept) => {
      // Assert on the API response
      const responseBody = JSON.parse(intercept.response.body);
      let user_id = responseBody.response.roles.records[0].id;
      cy.log("user_id=" + user_id);
      cy.intercept(
        "PUT",
        `/api/v1/apps/${appData.app_uuid}/roles/${user_id}`
      ).as("userRoleUpdate");
      cy.wait(5000);
      cy.get("table > tbody > tr").trigger("mouseover");
      appPanelPageObjects.getThreeDotsMenu().click({
        force: true,
        multiple: true,
      });
      appPanelPageObjects.getDeactivateUserRoleButton().click({
        force: true,
        multiple: true,
      });
      appPanelPageObjects.getSubmitButton().click();
    });
  }
);

And(
  "Admin clicks on the activate user role button under the three dots menu",
  () => {
    cy.wait("@getUserRole").then((intercept) => {
      // Assert on the API response
      const responseBody = JSON.parse(intercept.response.body);
      let user_id = responseBody.response.roles.records[0].id;
      cy.log("user_id=" + user_id);
      cy.intercept(
        "PUT",
        `/api/v1/apps/${appData.app_uuid}/roles/${user_id}`
      ).as("userRoleUpdate");
      cy.wait(5000);
      cy.get("table > tbody > tr").trigger("mouseover");
      appPanelPageObjects.getThreeDotsMenu().click({
        force: true,
        multiple: true,
      });
      appPanelPageObjects.getActivateUserRoleButton().click({
        force: true,
        multiple: true,
      });
      appPanelPageObjects.getSubmitButton().click();
    });
  }
);

And("Admin updates the user role form with the valid data", () => {
  cy.wait("@getUserRole").then((intercept) => {
    // Assert on the API response
    const responseBody = JSON.parse(intercept.response.body);
    let user_id = responseBody.response.roles.records[0].id;
    cy.log("user_id=" + user_id);
    cy.intercept("PUT", `/api/v1/apps/${appData.app_uuid}/roles/${user_id}`).as(
      "userRoleUpdate"
    );
    appPanelPageObjects.getRoleName().clear().type(userRole.updated_user_role);
    appPanelPageObjects.getSubmitButton().click({ force: true });
  });
});

Then(
  "Api response post update of the user role should have message {string} and status code {int}",
  (message, status_code) => {
    cy.wait("@userRoleUpdate").then((intercept) => {
      // Assert on the API response
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
      expect(intercept.response.statusCode).to.eq(status_code);
    });
  }
);

And(
  "Api response post update should have message {string} and status code {int}",
  (message, status_code) => {
    cy.wait("@userRoleUpdate").then((intercept) => {
      // Assert on the API response
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
      expect(intercept.response.statusCode).to.eq(status_code);
    });
  }
);

Then("Post deactivation user role should get deactivated", () => {
  cy.wait("@getUserRole").then((intercept) => {
    // Assert on the API response
    expect(
      JSON.parse(intercept.response.body).response.roles.records[0].is_active
    ).to.equal(false);
  });
});

Then("Post activation user role should get activated", () => {
  cy.wait("@getUserRole").then((intercept) => {
    // Assert on the API response
    expect(
      JSON.parse(intercept.response.body).response.roles.records[0].is_active
    ).to.equal(true);
  });
});

When("Admin lands on the user role tab", () => {
  cy.url().should("contain", "/user-roles/");
});

Then(
  "Api response post landing on user role tab should have message {string} and status code {int}",
  (message, status_code) => {
    cy.wait("@getUserRoleTab").then((intercept) => {
      // Assert on the API response
      expect(JSON.parse(intercept.response.body).response.message).to.equal(
        message
      );
      expect(intercept.response.statusCode).to.eq(status_code);
    });
  }
);
