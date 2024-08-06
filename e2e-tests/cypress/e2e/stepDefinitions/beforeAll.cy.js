before(() => {
  //Login functionality from command function
  // need to call from backend
  Cypress.on("uncaught:exception", (err, runnable) => {
    // returning false here prevents Cypress from
    // failing the test
    return false;
  });
});
