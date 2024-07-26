Feature: Task Management
    Background: Navigate to the Task Tab
        Given User navigates to task tab
    @focus
    Scenario: Admin wants to sync the tasks
        When Admin clicks on the sync task button
        Then Api response post syncing tasks should have message "Tasks synced successfully" and status code 200
    Scenario: Admin wants to verify that all the tasks are loaded
        When Validate the task tab URL
        And Task table should contain the following columns
            | Column_1 | Column_2  | Column_3 | Column_4       | Column_5 |
            | Task Id  | Task Name | Policy   | Schedule (UTC) | Status   |
        Then Api response post landing on tasks tab should have message "All app tasks fetched successfully" and status code 200
