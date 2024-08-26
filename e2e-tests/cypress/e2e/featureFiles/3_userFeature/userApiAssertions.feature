Feature: User Api Assertions
    Background: Navigates to the user tab
        Given Admin navigates to the user tab and gets the user data from fixture data
    # Scenario: Api assertion post landing on apps tab
    Scenario: Api assertion post landing on user tab
        And Validate the user tab URL
        Then Api response post landing on user tab should have message "Users fetched successfully" and status code 200
    Scenario: Api assertion post search
        When Admin clicks on the user table search button and Enters the valid data
        Then Api response post search should have message "Users fetched successfully" total records should be 1 and status code 200 in user table
    Scenario: Api assertion for deactivating the user
        When Admin clicks on the user table search button and Enters the valid data
        And Admin clicks on the deactivate user button under the three dots menu
        And Api response post update should have message "App User updated successfully." and status code 200
        Then Post deactivation user should get deactivated
    Scenario: Api assertion for activating the user
        When Admin clicks on the user table search button and Enters the valid data
        And Admin clicks on the activate user button under the three dots menu
        And Api response post update should have message "App User updated successfully." and status code 200
        Then Post activation user should get activated
# Scenario: Admin wants to update the user and also assert the api response
#     When Admin clicks on the user table search button and Enters the valid data
#     And Admin clicks on the edit user button under the three dots menu
#     And Admin updates the user form with the valid data
#     Then Api response post update should have message "App User updated successfully." and status code 200
