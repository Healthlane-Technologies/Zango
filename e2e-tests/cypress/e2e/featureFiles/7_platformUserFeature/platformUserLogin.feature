Feature: Platform User Login Management
    Background: User Navigates to the application URL
        Given Platform user navigates to the application URL

    Scenario: Platform user logs into the system
        When Platform user validates the application URL
        And Platform user login form is dispalyed with the following fields
            | field_name_1   | field_name_2   |
            | Enter Username | Email Password |
        And Platform user fills the login form with the valid details and click on the submit button
        Then Platform user should be successfully logged in and should be redirected to the application platform

    Scenario: Api assertion post platform user logs in
        When Platform user fills the login form with the valid details and click on the submit button
        Then Post logging into the application platform user should be activated

    Scenario: Api assertion post landing on the application platform
        When Platform user fills the login form with the valid details and click on the submit button
        Then Api response post landing on application platform should have message "All apps fetched successfully" and status code 200