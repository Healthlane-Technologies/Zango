Feature: Package Management
    Background: Navigate to the Package Tab
        Given User navigates to Package tab
    @focus
    Scenario: Admin wants to verify the contents of package tab
        When Validate the Package tab URL
        And Package table should contain the following columns
            | Column_1     | Column_2 | Column_3 | Column_4 |
            | Package Name | Version  | Status   | Status   |
        Then Api response post landing on Package tab should have status code 200

# Scenario Outline:Admin wants to install the packages
#     When Admin clicks on the package table search button and Enters the "<packages>"
#     And Admin clicks on the install package button under the three dots menu
#     And Install package form should contain following fields
#         | field_name_1 | field_name_2 |
#         | Package Name | Version      |
#     And Admin selects the version and submits the form
#     Then Api response post installation should have message "Package Installed" and status code 200

#     Examples:
#         | packages      |
#         | communication |
#         | crud          |
#         | frame         |
#         | login         |
#         | workflow      |
