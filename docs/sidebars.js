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
      type: "category",
      label: "Introduction",
      items: ["core/introduction", "core/framework-architecture"],
      collapsible: false,
    },
    {
      type: "category",
      label: "Getting Started",
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
          items: ["tutorials/todo-app/overview"],
        },
      ],
      collapsible: false,
    },
    {
      type: "category",
      label: "Framework Components",
      items: [
        {
          type: "category",
          label: "User Management",
          description: "Seamlessly manage application users.",
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
          description: "User roles with Role Based Access Control (RBAC).",
          collapsed: true,
          items: [
            "core/user-roles/overview",
            "core/user-roles/creating-a-user-role",
            "core/user-roles/deactivating-a-user-role",
            "core/user-roles/assigning-policies-to-user-roles",
            "core/user-roles/reserved-user-roles",
          ],
        },
        {
          type: "category",
          label: "Permissions Framework",
          description: "Permission rules and access control.",
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
          description:"Modular, extensible software components.",
          collapsed: true,
          items: [
            "core/packages-ecosystem/overview",
            "core/packages-ecosystem/installing-a-package",
          ],
        },
        {
          type: "category",
          label: "Async Tasks",
          description: "Seamlessly manage background tasks.",
          collapsed: true,
          items: [
            "core/async-tasks/overview",
            "core/async-tasks/creating-an-async-task",
            "core/async-tasks/manually-triggering-async-tasks",
            "core/async-tasks/scheduling-async-tasks",
            "core/async-tasks/syncing-and-viewing-async-tasks",
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
      type: "category",
      label: "Development Workflow",
      items: [
        {
          type: "category",
          label: "Modules",
          description: "Code organisation within your Zango app.",
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
          description: "Implement Django Views within your Zango app.",
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
          description: "Leverage Django’s Templates.",
          collapsed: true,
          items: ["core/templates/overview"],
        },
        {
          type: "category",
          label: "Models",
          description: "Django models adapted for Zango.",
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
    require("./pkgsSidebar") ? require("./pkgsSidebar") : null,
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
