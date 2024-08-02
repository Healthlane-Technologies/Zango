beforeEach(() => {
  //Login functionality from command function
  // need to call from backend
  cy.visit("http://localhost:3000/platform/apps");
  Cypress.on("uncaught:exception", (err, runnable) => {
    // returning false here prevents Cypress from
    // failing the test
    return false;
  });
});
