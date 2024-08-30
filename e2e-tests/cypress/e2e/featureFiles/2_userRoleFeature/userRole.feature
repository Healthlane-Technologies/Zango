Feature: User Role Creation and Validation
    Background: Navigates to the user role tab
        Given Admin navigates to the user role tab and gets the user role data from fixture data

    Scenario: User role creation with valid data
        When Admin clicks on the new user role button on the user role page
        And Admin creates dynamic data for user role creation
        And Add user role form is displayed with the following fields
            | field_name_1 | field_name_2 |
            | Role Name    | Policy       |
        And Admin fills up the user role form with the valid data and submits the form
        Then User role should be successfully added and admin should be redirected to the table view
        And Admin also wants to assert the Api response post user role addition
        Then Api response post user role creation should have message "User Role Created Successfully" and status code 200

    Scenario: Required fields validation for user role form
        When Admin clicks on the new user role button on the user role page
        And Admin skips the mandatory fields
        Then Required field error message for user role form should be displayed

    Scenario: User role creation with existing role name
        When Admin clicks on the new user role button on the user role page
        And Admin fills up the user role form with the valid data and submits the form
        Then Error message for duplication of user role should be displayed

    Scenario: User role update with existing role name
        When Admin clicks on the user role table search button and Enters the valid data
        And Admin clicks on the edit user role button under the three dots menu
        And Admin fills up the edit user role form with the existing data and submits the form
        Then Error message for duplication of user role should be displayed

    Scenario: Table data validation post user role creation
        When Validate the user role tab URL
        And User role table should contain the following columns
            | Column_1 | Column_2  | Column_3        | Column_4     |
            | Role     | Policy(s) | Active/Inactive | No. of Users |
        And Admin clicks on the user role table search button and Enters the valid data
        Then User role table row should contain the valid data
