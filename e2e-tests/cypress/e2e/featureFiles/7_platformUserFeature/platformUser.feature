Feature: Platform User Management
    Background: Navigates to the application platform
        Given Admin navigates to the user management tab and gets the platform user data from fixtures

    Scenario: New platform user creation by the admin
        When Admin clicks on the new user button on the user management page
        And Admin creates the dynamic data of the platform user
        And Add platform user form is dispalyed with the following fields
            | field_name_1 | field_name_2 | field_name_3 | field_name_4 |
            | Full Name    | Email        | Password     | Apps Access  |
        And Admin fills up the platform user form with valid data and submits the form
        Then Platform User should be successfully added and admin should be redirected to the table view
        And Admin also wants to assert the Api response post platform user creation
        Then Api response post platform user creation should have message "Platform User created successfully." and status code 200

    Scenario: Required fields validation for platform user form
        When Admin clicks on the new user button on the user management page
        And Admin skips the mandatory fields on the platform user form
        Then Required field error message should be displayed on the platform user form

    Scenario: Platform User creation with existing platform user name
        When Admin clicks on the new user button on the user management page
        And Admin fills up the platform user form with valid data and submits the form
        Then Error message for duplication of platform user management should be displayed

    Scenario: Table data validation post platform user creation
        When Admin wants to validate the user management tab URL
        And User management table should contain the following columns
            | Column_1 | Column_2                  | Column_3 | Column_4    | Column_5                 |
            | User Id  | User Name Active/inactive | Email    | Apps Access | Last Login / Date Joined |
        And Admin clicks on the user management table search button and Enters the valid data
        Then User management table row should contain the valid data