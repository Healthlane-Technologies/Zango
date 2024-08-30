Feature: User Creation and Validation
    Background: Navigates to the user tab
        Given Admin navigates to the user tab and gets the user data from fixture data

    Scenario: user creation with valid data
        When Admin clicks on the new user button on the user page
        And Admin creates the dynamic data of the user creation
        And Add user form is dispalyed with the following fields
            | field_name_1 | field_name_2 | field_name_3 | field_name_4 | field_name_5 |
            | Full Name    | Email        | Mobile       | Password     | User Role    |
        And Admin fills up the user form with valid data and submits the form
        Then User should be successfully addded and admin should be redirected to the table view
        And Admin also wants to assert the Api response post user addition
        Then Api response post user creation should have message "App User created successfully." and status code 200
    Scenario: Required fields validation for user form
        When Admin clicks on the new user button on the user page
        And Admin skips the mandatory fields on user form
        Then Required field error message for user from should be displayed
    Scenario: User creation with existing user name
        When Admin clicks on the new user button on the user page
        And Admin fills up the user form with valid data and submits the form
        Then Error message for duplication of user should be displayed

    Scenario: Table data validation post user creation
        And Validate the user tab URL
        And User table should contain the following columns
            | Column_1 | Column_2                  | Column_3 | Column_4 | Column_5          | Column_6                 | Column_7             |
            | User Id  | User Name Active/inactive | Mobile   | Email    | Management Access | Last Login / Date Joined | Password Change date |
        And Admin clicks on the user table search button and Enters the valid data
        Then User table row should contain the valid data
