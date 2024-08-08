Feature: App Launch and Validation
    Scenario: App Launch with valid data
        Given Admin logins successfully and lands on the home page of App panel
        When Admin clicks on the app launch button on homepage
        And Admin fills the app launch form with the valid data and submits the form
        Then App should be successfully Launched and also the Api response should have message "App Launch Initiated Successfully" and status code 200

    Scenario: App launch with invalid data
        When Admin clicks on the app launch button on homepage
        And Admin fills the app launch form with the invalid data and submits the form
        Then Error message for invalid app name should be displayed and status code of api response should be 500

    Scenario: App launch with existing app data
        When Admin clicks on the app launch button on homepage
        And Admin fills the app launch form with the valid data and submits the form
        Then Error message for duplication app name should be displayed and status code of api response should be 500

