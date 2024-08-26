Feature: Policy Management
    Background: Navigate to the Policies Tab
        Given  User navigates to policies tab
    Scenario: Admin wants to verify that all the policies are loaded
        When Validate the policies tab URL
        And Policy table should contain the following columns
            | Column_1  | Column_2    | Column_3      | Column_4    | Column_5 |
            | Policy Id | Policy Name | Configuration | Description | Roles    |
        Then Api response post landing on policies tab should have message "All policies fetched successfully" and status code 200

    Scenario: Admin wants to sync the policies
        When Admin clicks on the sync policy button
        Then Api response post syncing policies should have message "Policies synced successfully" and status code 200
