// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
/// <reference types="cypress" />

//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })
import "cypress-file-upload";

Cypress.Commands.add("login", (username, password) => {
  cy.visit("http://localhost:8000/auth/login/?next=/platform/");
  cy.get('[type="text"]').type(username);
  cy.get('[type="password"]').type(password);
  cy.get("button").click();
});

Cypress.Commands.add("multipleLocator", (locator1, locator2) => {
  cy.get("#root").then((body) => {
    if (body.find(locator1).length > 0) {
      cy.get(locator1).click();
    } else if (body.find(locator2).length > 0) {
      cy.get(locator2).click();
    } else {
      throw new Error(`Neither locator found: ${locator1}, ${locator2}`);
    }
  });
});
