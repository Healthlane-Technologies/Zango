Feature: App Launch and Validation
    Background: Navigate to the home page of App Panel
        Given Admin logins successfully and lands on the home page of App panel

    Scenario: App Launch with valid data
        When Admin clicks on the app launch button on homepage
        And Admin fills the app launch form with the valid data and submits the form
        Then App should be successfully Launched and also the Api response should have message "App Launch Initiated Successfully" and status code 200
