/**
 * Creating a sidebar enables you to:
 create an ordered group of docs
 render a sidebar for each doc of that group
 provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */

// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docsSidebar: [   
    {
      type: 'category', 
      label: 'Introduction',
      items: [
        "core/introduction",
        "core/framework-architecture", 
      ],
      collapsible: false
    },
    {
      type: 'category', 
      label: 'Getting Started',
      items: [
        "core/quickstart",
        {
          type: "category",
          label: "Installing Zango",
          link: {
            type: "generated-index",
          },
          collapsed: true,
          items: [
            "core/getting-started/installing-zango/python-venv",
            "core/getting-started/installing-zango/docker",
            "core/getting-started/installing-zango/gitpod",
          ],
        },
        {
          type: "category",
          label: "Setting up Zango project",
          link: {
            type: "generated-index",
          },
          collapsed: true,
          items: [
            "core/setting-up-zango-project/overview",
            "core/setting-up-zango-project/creating-zango-project",
            "core/setting-up-zango-project/launching-an-app",
          ],
        },
        "core/getting-started/creating-a-hello-world-app",
        {
          type: "category",
          label: "Tutorials",
          link: {
            type: "generated-index",
          },
          collapsed: true,
          items: [
            "tutorials/todo-app/overview",
          ],
        },
      ],
      collapsible: false
    },
    {
      type: 'category', 
      label: 'Framework Components',
      items: [
        {
          type: "category",
          label: "User Management",
          collapsed: true,
          items: [
            "core/user-management/overview",
            "core/user-management/adding-users",
            "core/user-management/updating-user-roles",
            "core/user-management/viewing-users",
          ],
        },
        {
          type: "category",
          label: "User Roles",
          collapsed: true,
          items: [
            "core/user-roles/overview",
            "core/user-roles/creating-a-user-role",
            "core/user-roles/deactivating-a-user-role",
            "core/user-roles/assigning-policies-to-user-roles",
            "core/user-roles/reserved-user-roles"
          ],
        },
        {
          type: "category",
          label: "Permissions Framework",
          collapsed: true,
          items: [
            "core/permission-framework/overview",
            {
              type: "category",
              label: "Permissions",
              collapsed: true,
              items: [
                "core/permission-framework/permissions/overview",
                "core/permission-framework/permissions/creating-permissions",
                "core/permission-framework/permissions/using-permissions",
                "core/permission-framework/permissions/syncing-and-viewing-permissions",
              ],
            },
            {
              type: "category",
              label: "Policies",
              collapsed: true,
              items: [
                "core/permission-framework/policies/overview",
                "core/permission-framework/policies/creating-a-policy",
                "core/permission-framework/policies/archiving-a-policy",
                "core/permission-framework/policies/assigning-policies",
                "core/permission-framework/policies/syncing-policy",
                "core/permission-framework/policies/viewing-policies",
                "core/permission-framework/policies/policy-config-json",
              ],
            },
          ],
        },
        "core/getting-started/zango-cli",
        {
          type: "category",
          label: "Packages Ecosystem",
          collapsed: true,
          items: [
            "core/packages-ecosystem/overview",
            "core/packages-ecosystem/installing-a-package"
          ],
        },
        {
          type: "category",
          label: "Async Tasks",
          collapsed: true,
          items: [
            "core/async-tasks/overview",
            "core/async-tasks/creating-an-async-task",
            "core/async-tasks/manually-triggering-async-tasks",
            "core/async-tasks/scheduling-async-tasks",
            "core/async-tasks/syncing-and-viewing-async-tasks"
          ],
        },
      ],
      collapsible: true,
      link: {
        type: "generated-index",
        title: "Zango Framework Components",
      },
    },
    {
      type: 'category', 
      label: 'Development Workflow',
      items: [
        {
          type: "category",
          label: "Modules",
          collapsed: true,
          items: [
            "core/modules/overview",
            "core/modules/creating-a-module",
            "core/modules/registering-a-module",
          ],
        }, 
        {
          type: "category",
          label: "Views and Routes",
          collapsed: true,
          items: [
            "core/views-and-routes/overview",
            "core/views-and-routes/creating-a-view",
            "core/views-and-routes/assigning-route-to-a-view",
          ],
        }, 
        {
          type: "category",
          label: "Templates",
          collapsed: true,
          items: [
            "core/templates/overview"
          ],
        }, 
        {
          type: "category",
          label: "Models",
          collapsed: true,
          items: [
            "core/ddms/overview",
            "core/ddms/creating-a-ddm",
            "core/ddms/ddm-field-types",
            "core/ddms/migrating-ddms",
          ],
        }, 
      ],
      collapsible: true,
      link: {
        type: "generated-index",
      },
    },
    "core/enterprise-readiness",
    {
      type: 'category', 
      label: 'Packages',
      link: {
        type: "generated-index",
      },
      items: [
        {
          type: "category",
          label: "Basic Auth",
          collapsed: true,
          items: [
            "packages/basic-auth/overview",
            "packages/basic-auth/start",
            "packages/basic-auth/accessing-login-page",
            "packages/basic-auth/configuring-login-page-ui",
            "packages/basic-auth/setting-default-landing-route",
            
          ],
        },
        {
          type: "category",
          label: "Frame",
          collapsed: true,
          items: [
            "packages/frame/overview",
            "packages/frame/installation",
            "packages/frame/config-options",
            "packages/frame/configuring-menu",
            "packages/frame/redirecting-to-frame-view",
          ],
        }, 
        {
          type: "category",
          label: "Crud",
          collapsed: true,
          items: [
            "packages/crud/overview",
            "packages/crud/crud-installation",
            {
              type: "category",
              label: "Crud view",
              collapsed: true,
              items: [
                "packages/crud/crud-view/creating-crudview",
                "packages/crud/crud-view/import-crudview-modules",
                "packages/crud/crud-view/setting-configuration",
                "packages/crud/crud-view/permissions-setup",
                "packages/crud/crud-view/updating-app-theme",
              ],
            },
            {
              type: "category",
              label: "Tables",
              collapsed: true,
              items: [
                "packages/crud/tables/overview",
                "packages/crud/tables/creating-table-class",
                "packages/crud/tables/table-columns",
                "packages/crud/tables/custom-display-methods",
                "packages/crud/tables/row-action-methods",
                "packages/crud/tables/tables-api-reference",
              ],
            },
            {
              type: "category",
              label: "Form",
              collapsed: true,
              items: [
                "packages/crud/forms/creating-form-class",
                "packages/crud/forms/form-fields",
                "packages/crud/forms/best-practices",
                "packages/crud/forms/forms-api-reference",
              ],
            },
          ],
        },
        {
          type: "category",
          label: "Workflow",
          collapsed: true,
          items: [
            "packages/workflow/overview",
            "packages/workflow/installation",
            "packages/workflow/configuring-workflow",
            "packages/workflow/linking-crudview",
            {
              "type": "category",
              "label": "Creating Transitions",
              "collapsed": true,
              "items": [
                "packages/workflow/understanding-transitions",
                "packages/workflow/status-transitions",
                "packages/workflow/form-based-transition",
                "packages/workflow/executing-transitions"
              ]
            }
          ],
        },   
        {
          type: "category",
          label: "Communication",
          collapsed: true,
          items: [
            "packages/communication/overview",
            "packages/communication/installation",
            {
              type: "category",
              label: "Email",
              collapsed: true,
              items: [
                "packages/communication/email/introducing-emails",
                "packages/communication/email/activating-email",
                "packages/communication/email/adding-smtp-imap",
                "packages/communication/email/configure-imap-settings",
                {
                  type: "category",
                  label: "Sending Email",
                  collapsed: true,
                  items: [
                    "packages/communication/email/from-codebase",
                    "packages/communication/email/from-communication-dashboard",
                    "packages/communication/email/from-send-api",
                  ],
                },
                {
                  type: "category",
                  label: "Receiving Email",
                  collapsed: true,
                  items: [
                    "packages/communication/email/receive-email",
                    "packages/communication/email/receive-task",
                    "packages/communication/email/send-email",
                  ],
                },
              ],
            },
            {
              type: "category",
              label: "SMS",
              collapsed: true,
              items: [
                "packages/communication/sms/introducing-sms",
                "packages/communication/sms/activating-sms",
                {
                  type: "category",
                  label: "Adding infobip service",
                  collapsed: true,
                  items: [
                    "packages/communication/sms/installing-infobip",
                    "packages/communication/sms/configuring-infobip",
                  ],
                },  
                {
                  type: "category",
                  label: "Sending SMS",
                  collapsed: true,
                  items: [
                    "packages/communication/sms/from-sms-codebase",
                    "packages/communication/sms/from-sms-dashboard",
                    "packages/communication/sms/from-sms-api",
                  ],
                }, 
              ],
            },
            {
              type: "category",
              label: "Telephony",
              collapsed: true,
              items: [
                "packages/communication/telephony/introducing-telephony",
                {
                  type: "category",
                  label: "Adding NICE service",
                  collapsed: true,
                  items: [
                    "packages/communication/telephony/installing-nice",
                    "packages/communication/telephony/configuring-nice",
                    "packages/communication/telephony/adding-nice-agent",
                  ],
                }, 
                {
                  type: "category",
                  label: "Configuring Agent Dialer",
                  collapsed: true,
                  items: [
                    "packages/communication/telephony/script-in-frame",
                    "packages/communication/telephony/adding-placecall-button",
                  ],
                }, 
              ],
            },
          ],
        },
        {
          type: "category",
          label: "Advanced auth",
          collapsed: true,
          items: [
            "packages/advanced-auth/overview",
            "packages/advanced-auth/installation",
            "packages/advanced-auth/signup-auth-configs",
            "packages/advanced-auth/theme-configs",
            "packages/advanced-auth/notifications-configs"
          ],
        },
        {
          type: "category",
          label: "Appointment",
          collapsed: true,
          items: [
            "packages/appointment/overview",
            {
                "type": "category",
                "label": "Getting Started",
                "collapsed": false,
                "items": [
                  "packages/appointment/getting-started/installation",
                  "packages/appointment/getting-started/initialize-data-model",
                  "packages/appointment/getting-started/initialize-views"
                ]
            },
            {
                "type": "category",
                "label": "Configurations",
                "collapsed": false,
                "items": [
                  "packages/appointment/configurations/participants",
                  "packages/appointment/configurations/hosts",
                  "packages/appointment/configurations/channels",
                  "packages/appointment/configurations/custom-workflow",
                  "packages/appointment/configurations/notes",
                  "packages/appointment/configurations/crud-configs",
                  "packages/appointment/configurations/communication-configs",
                  "packages/appointment/configurations/phone-numbers",
                  "packages/appointment/configurations/address",
                  "packages/appointment/configurations/reminders",
                  {
                    "type": "category",
                    "label": "Notifications",
                    "collapsed": false,
                    "items": [
                      "packages/appointment/notifications/channels",
                      "packages/appointment/notifications/email-template",
                      "packages/appointment/notifications/on-status-update",
                      "packages/appointment/notifications/recipients",
                      "packages/appointment/notifications/content"
                    ]
                }
                ]
            }
          ],
        },
      ],
      collapsible: true
    },
    // {
    //   "type": "category",
    //   "label": "Deployment",
    //   "collapsed": false,
    //   "items": [
    //     "core/deployment/overview",
    //     {
    //       "type": "category",
    //       "label": "Deploying the todo app",
    //       "collapsed": false,
    //       "items": [
    //         "core/deployment/overview"
    //       ]
    //     },
    //   ]
    // },
    // {
    //   "type": "category",
    //   "label": "Contributing to Zango",
    //   "link": {
    //     "type": "generated-index"
    //   },
    //   "collapsed": false,
    //   "items": [
    //       "core/contributing/overview",
    //       "core/contributing/setting-up-environment",
    //   ]
    // },
  ],
};

module.exports = sidebars;
