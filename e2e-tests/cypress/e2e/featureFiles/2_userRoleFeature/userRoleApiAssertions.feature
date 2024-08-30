Feature: User Role Api Assertions

    Background: Navigates to the user role tab
        Given Admin navigates to the user role tab and gets the user role data from fixture data

    Scenario: Api assertion post landing on user role tab
        When Admin lands on the user role tab
        Then Api response post landing on user role tab should have message "All roles fetched successfully" and status code 200

    Scenario: Api assertion post search
        When Admin clicks on the user role table search button and Enters the valid data
        Then Api response post search should have message "All roles fetched successfully" total records should be 1 and status code 200 in user role table

    Scenario: Api assertion for deactivating the user role
        When Admin clicks on the user role table search button and Enters the valid data
        And Admin clicks on the deactivate user role button under the three dots menu
        And Api response post update of the user role should have message "User Role Updated Successfully" and status code 200
        Then Post deactivation user role should get deactivated

    Scenario: Api assertion for activating the user role
        When Admin clicks on the user role table search button and Enters the valid data
        And Admin clicks on the activate user role button under the three dots menu
        And Api response post update of the user role should have message "User Role Updated Successfully" and status code 200
        Then Post activation user role should get activated

    Scenario: Admin wants to update the user role and also assert the api response
        When Admin clicks on the user role table search button and Enters the valid data
        And Admin clicks on the edit user role button under the three dots menu
        And Admin updates the user role form with the valid data
        Then Api response post update of the user role should have message "User Role Updated Successfully" and status code 200
