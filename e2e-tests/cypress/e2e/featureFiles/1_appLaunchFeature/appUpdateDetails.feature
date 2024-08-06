Feature: App Update and Validation
    Background: Navigate to the details view of App
        Given Admin logins successfully and lands on the details view of App

    Scenario: Api assertion post landing on app details view
        When Validate the app configuration URL
        Then Api response post landing on the app configuration should have same app name and app uuid

    Scenario: Update app details with valid data
        When Admin clicks on the update details button in the app details view
        And App update form should be displayed with the following fields
            | field_name_1 | field_name_2 | field_name_3 | field_name_4    | field_name_5 | field_name_6 | field_name_7 | field_name_8     |
            | App Name     | Description  | Upload Logo  | Upload Fav Icon | Domain       | Time Zone    | Date Format  | Date Time Format |
        And Admin fills the app details form with the valid data and submits the form
        Then App details should be successfully updated and also the Api response should have message "App Settings Updated Successfully" and status code 200
        When Admin lands back on the details view
        Then App details should be updated as expected
