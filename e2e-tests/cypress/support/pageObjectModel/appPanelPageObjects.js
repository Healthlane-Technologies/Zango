/*Locators for the below field types:

  1. Text Field: [data-cy="text_field"]
  2. Text Area: [data-cy="text_area"]
  3. Numeric Field: [data-cy="numeric_field"]
  3. File Upload: [data-cy="file_upload"]
  4. Dropdown Field: [data-cy="dropdown_field"]
  5. Dropdown Values: [data-cy="dropdown_values"]
  6. Multi-Select Field: [data-cy="multi_select_values"]
  7. Three Dots Menu

*/

const appPanelPageObjects = {
  getDropDownButton: () => cy.get('[data-cy = "dropdown_field"]'),
  getDropDownValues: () => cy.get('[data-cy = "dropdown_values"]>div>div>li'),
  getVersion: () =>
    cy.get('[data-cy = "dropdown_values"]>div>div>li:nth-child(1)'),
  getMultiSelectDropDownValues: () =>
    cy.get('[data-cy = "multi_select_values"]>div>div>li'),
  getFormLabel: () => cy.get("div:nth-child(1) > label"),
  getTimeZoneFieldText: () => cy.get("div:nth-child(6) > label"),
  getDateFormatFieldText: () => cy.get("div:nth-child(7) > label"),
  getDateTimeFormatFieldText: () => cy.get("div:nth-child(8) > label"),
  getErrorMessage: () => cy.get(".text-[#cc3300]"),
  getThreeDotsMenu: () => cy.get('[data-cy="three_dots_menu"]'),
  getFilterButton: () => cy.get("#is_active"),
  getFilterOptions: () => cy.get('ul[role="listbox"]'),
  getMenuList: () => cy.get('[data-cy="menu_section"]'),
  getTableBody: () =>
    cy.get("#root > main > div> div> div > div > table > tbody"),
  getUserRolePageTitle: () => cy.get("#root > main > div> div > div > a"),
  getTableColumnOneHeader: () => cy.get("table > thead > tr > th:nth-child(1)"),
  //Menu Tabs Page Objects
  getAppConfigurationTab: () => cy.get('[data-cy="app_configuration"]'),
  getAppThemeConfigurationTab: () =>
    cy.get('[data-cy="app_theme_configuration"]'),
  getAppLaunchButton: () => cy.get('[data-cy="launch_app_button"]'),
  getTextField: () => cy.get('[data-cy="text_field"]'),
  getTextArea: () => cy.get('[data-cy="text_area"]'),
  getuserRolesTab: () => cy.get('[data-cy="user_roles"]'),
  getuserTab: () => cy.get('[data-cy="user_management"]'),
  getPoliciesTab: () => cy.get('[data-cy="policies"]'),
  getTasksTab: () => cy.get('[data-cy="task_management"]'),
  getPackagesTab: () => cy.get('[data-cy="packages"]'),
  getApplicationObjectsTab: () => cy.get('[data-cy="application_objects"]'),
  getFrameworkObjectsTab: () => cy.get('[data-cy="framework_objects"]'),
  //launch app form
  getAppNameField: () => cy.get('input[ name="name"]'),
  getAppDescriptionField: () => cy.get('textarea[name="description"]'),
  getSubmitButton: () =>
    cy.get("#headlessui-dialog-panel-:r4: > form > div> button"),
  //Select the app from the list
  getAllAppList: () => cy.get('[data-cy="app_list"]'),
  //Home Page Page Objects
  getLaunchAppButton: () => cy.get('[data-cy="launch_app_button"]'),
  getAppID: () => cy.get('[data-cy="app_id"]'),
  getAppName: () => cy.get('[data-cy="app_name"]'),
  getAppDescription: () => cy.get('[data-cy="app_description"]'),
  getAppDomainUrl: () => cy.get('[data-cy="domain_url"]'),
  getAddDomainButton: () => cy.get(".w-fit > .font-lato"),
  getEnterDomainURl: () => cy.get(".flex-col > .relative > .w-full"),
  //App Details View Page Objects
  getAppNameDetailsView: () => cy.get('[data-cy="app_name_details_view"]'),
  getUpdateDetailsButton: () => cy.get('[data-cy="update_details_button"]'),
  getUpdateDetails: () =>
    cy.get("#root > main > div> div> div > button > span"),
  getLogoUploadButton: () => cy.get("#logo"),
  getFavIconButton: () => cy.get("#fav_icon"),
  getDomain: () => cy.get("div:nth-child(5) > label"),
  getTimeZone: () => cy.get("#timezone"),
  getDateFormat: () => cy.get("#date_format"),
  getDateTimeFormat: () => cy.get("#datetime_format"),
  getDateFormatList: () => cy.get("#headlessui-listbox-options-:r576:"),
  getUpdateSubmitButton: () => cy.get('button[type="submit"]'),
  //Error message modal
  getErrorMessage: () => cy.get('[data-cy="error_message"]'),
  getGoBackButton: () => cy.get('[data-cy="go_back_button"]'),
  //App details page
  getRowData: () =>
    cy.get("#root > main > div> div> table > tbody > tr:nth-child(1)"),
  //App details view page objects
  getFirstRowValue: () =>
    cy.get("table > tbody > tr:nth-child(1) > td:nth-child(1)"),
  getSecondRowValue: () =>
    cy.get("table > tbody > tr:nth-child(2) > td:nth-child(1)"),
  getThirdRowValue: () =>
    cy.get("table > tbody > tr:nth-child(3) > td:nth-child(1)"),
  getFourthRowValue: () =>
    cy.get("table > tbody > tr:nth-child(4) > td:nth-child(1)"),
  getFifthRowValue: () =>
    cy.get("table > tbody > tr:nth-child(5) > td:nth-child(1)"),
  getSixthRowValue: () =>
    cy.get("table > tbody > tr:nth-child(6) > td:nth-child(1)"),
  getSeventhRowValue: () =>
    cy.get("table > tbody > tr:nth-child(7) > td:nth-child(1)"),
  //
  getColumnOneValue: () =>
    cy.get("table > tbody > tr:nth-child(1) > td:nth-child(2)"),
  getColumnTwoValue: () =>
    cy.get("table > tbody > tr:nth-child(2) > td:nth-child(2)"),
  getColumnThreeValue: () =>
    cy.get("table > tbody > tr:nth-child(3) > td:nth-child(2)"),
  getColumnFourValue: () =>
    cy.get("table > tbody > tr:nth-child(4) > td:nth-child(2)"),
  getColumnFiveValue: () =>
    cy.get("table > tbody > tr:nth-child(5) > td:nth-child(2)"),
  getColumnSixValue: () =>
    cy.get("table > tbody > tr:nth-child(6) > td:nth-child(2)"),
  getColumnSevenValue: () =>
    cy.get("table > tbody > tr:nth-child(7) > td:nth-child(2)"),
  // for app user roles
  getNewUserRole: () => cy.get('[data-cy="add_user_role_button"]'),
  getUserRolePageTitle: () =>
    cy.get("#headlessui-dialog-title-:rg: > div > h4"),
  getRoleName: () => cy.get('[data-cy="text_field"]'),
  getPolicy: () => cy.get("#policies"),
  getSubmitButton: () => cy.get("button[type = 'submit']"),
  getFirstRow: () =>
    cy.get(
      "#root > main > div > div> div > div> table > tbody > tr:nth-child(1)"
    ),
  getColumn1: () =>
    cy.get(
      "#root > main > div > div> div > div> table > tbody > tr:nth-child(1)> td:nth-child(1) > div"
    ),
  getColumn2: () =>
    cy.get(
      "#root > main > div > div> div > div> table > tbody > tr:nth-child(1)> td:nth-child(2) > div"
    ),
  getColumn3: () =>
    cy.get(
      "#root > main > div > div> div > div> table > tbody > tr:nth-child(1)> td:nth-child(3) > div"
    ),
  getColumn4: () =>
    cy.get(
      "#root > main > div > div> div > div> table > tbody > tr:nth-child(1)> td:nth-child(4) > div"
    ),
  getThreeDotsButton: () =>
    cy.get("div > table > tbody >tr > td:nth-child(7).h-full"),
  getEditUserPageTitle: () =>
    cy.get("#headlessui-dialog-title-:r2c: > div > h4"),
  getSearchBar: () =>
    cy.get('[placeholder="Search User roles by role / policy(s)"]'),
  getShowEditButton: () =>
    cy.get("table > tbody > tr:nth-child(1) > td:nth-child(6)"),
  getfullfirstrow: () => cy.get("table > tbody > tr:nth-child(1)"),
  getEditSlot: () =>
    cy.get(
      "#root > main > div.flex.grow.flex-col.gap-[20px] > div.flex.grow.flex-col.overflow-x-auto > div > div.relative.flex.grow.overflow-x-auto.overflow-y-auto > table > tbody > tr:nth-child(1) > td.flex.h-full.w-[188px].flex-col.border-b.border-[#F0F3F4].px-[20px].py-[14px].group-hover:hidden"
    ),
  getDeactivateUserRoleButton: () =>
    cy.get('[data-cy="deactivate_user_role_button"]'),
  getActivateUserRoleButton: () =>
    cy.get('[data-cy="activate_user_role_button"]'),
  getEditUserRoleButton: () => cy.get('[data-cy="edit_user_role_button"]'),

  //for Users tab
  getNewPageTitle: () => cy.get("#headlessui-dialog-title-:r3s: > div > h4"),
  getUserFullName: () => cy.get('[data-cy="text_field"]').eq(0),
  getUserEmail: () => cy.get('[data-cy="text_field"]').eq(1),
  getUserMobileNumber: () => cy.get('[data-cy="numeric_field"]'),
  getUserPassword: () => cy.get('[data-cy="text_field"]').eq(2),
  getUserRoles: () => cy.get('[data-cy="dropdown_field"]'),
  getUserDropdown: () => cy.get('[data-cy="multi_select_values"]'),
  getSubmitButton: () => cy.get("button[type = 'submit']"),
  getUserColumnOneHeader: () => cy.get("table > thead > tr > th:nth-child(1)"),
  getUserSearchBar: () =>
    cy.get(
      '[placeholder="Search Users by name / ID / role(s) / mobile / email"]'
    ),
  getAddUser: () => cy.get('[data-cy="add_user_button"]'),
  getNewUser: () => cy.get('[data-cy="new_user_button"]'),
  getFirstRowValue: () =>
    cy.get("table > tbody > tr:nth-child(1) > td:nth-child(1)"),
  getUserTableValue: () =>
    cy.get("table > tbody > tr:nth-child(1) > td:nth-child(2)"),
  getDeactivateUserButton: () => cy.get('[data-cy="deactivate_user_button"]'),
  getActivateUserButton: () => cy.get('[data-cy="activate_user_button"]'),
  //for policy tab
  getSyncPolicyButton: () => cy.get('[data-cy = "sync_policy_button"]'),
  getEditFormTitle: () => cy.get('[class*="font-semibold"]').eq(0),
  getPolicyName: () => cy.get("#name"),
  getPolicyDescription: () => cy.get("#description"),
  getPolicyRoles: () => cy.get("#roles"),
  getPolicySaveButton: () =>
    cy.get("#headlessui-dialog-panel-:rv:> form > div > button"),
  //for task tab
  getSyncTaskButton: () => cy.get('[data-cy = "sync_task_button"]'),
  //for packages tab
  getPackageSearchBar: () => cy.get('[placeholder="Search Packages by name"]'),
};

export default appPanelPageObjects;
