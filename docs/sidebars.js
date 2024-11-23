/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */

// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docsSidebar: [
    "core/introduction",
    "core/platform-architecture",
    {
      type: "category",
      label: "Getting Started",
      link: {
        type: "generated-index",
      },
      collapsed: true,
      items: [
        {
          type: "category",
          label: "Installing Zango",
          collapsed: true,
          items: [
            "core/getting-started/installing-zelthy/manual",
            "core/getting-started/installing-zelthy/docker",
            "core/getting-started/installing-zelthy/gitpod",
          ],
        },
        "core/getting-started/accessing-app-panel",
      ],
    },
    {
      type: "category",
      label: "Building your first App",
      link: {
        type: "generated-index",
      },
      collapsed: true,
      items: [
        "core/spinning-up-an-app/launch-the-app",
        "core/spinning-up-an-app/intializing-app-codebase",
        "core/spinning-up-an-app/switching-to-app-view",
        "core/spinning-up-an-app/updating-app-settings",
        "core/spinning-up-an-app/updating-app-theme",
      ],
    },
    {
      type: "category",
      label: "User Roles",
      link: {
        type: "doc",
        id: "core/user-roles/overview",
      },
      collapsed: true,
      items: [
        "core/user-roles/creating-a-user-role",
        "core/user-roles/assigning-policies-to-user-roles",
        "core/user-roles/deactivating-a-user-role",
        "core/user-roles/reserved-user-roles",
      ],
    },
    {
      type: "category",
      label: "User Management",
      link: {
        type: "doc",
        id: "core/user-management/overview",
      },
      collapsed: true,
      items: [
        "core/user-management/viewing-users",
        "core/user-management/adding-users",
        // 'documentation/user-management/assigning-policies-to-users',
        "core/user-management/updating-user-roles",
      ],
    },
    {
      type: "category",
      label: "Permission Framework",
      link: {
        type: "doc",
        id: "core/permission-framework/overview",
      },
      collapsed: true,
      items: [
        // {
        //   type: 'category',
        //   label: 'Permissions',
        //   link: {
        //     type: 'doc',
        //     id: 'documentation/permission-framework/permissions/overview',
        //   },
        //   collapsed: true,
        //   items: [
        //     'documentation/permission-framework/permissions/creating-permissions',
        //     'documentation/permission-framework/permissions/syncing-and-viewing-permissions',
        //     'documentation/permission-framework/permissions/using-permissions',
        //     'documentation/permission-framework/permissions/custom-permissions',
        //   ],
        // },
        {
          type: "category",
          label: "Policies",
          link: {
            type: "doc",
            id: "core/permission-framework/policies/overview",
          },
          collapsed: true,
          items: [
            "core/permission-framework/policies/viewing-policies",
            "core/permission-framework/policies/creating-a-policy",
            "core/permission-framework/policies/syncing-policy",
            "core/permission-framework/policies/assigning-policies",
            "core/permission-framework/policies/policy-config-json",
            // 'documentation/permission-framework/policies/editing-policy-config',
            // 'documentation/permission-framework/policies/archiving-a-policy',
          ],
        },
      ],
    },
    {
      type: "category",
      label: "Packages",
      link: {
        type: "doc",
        id: "core/packages/overview",
      },
      collapsed: true,
      items: ["core/packages/installing-a-package"],
    },
    {
      type: "category",
      label: "Development Workflow",
      link: {
        type: "generated-index",
      },
      collapsed: true,
      items: [
        {
          type: "category",
          label: "Modules",
          link: {
            type: "doc",
            id: "core/modules/overview",
          },
          collapsed: true,
          items: [
            "core/modules/creating-a-module",
            "core/modules/registering-a-module",
          ],
        },
        {
          type: "category",
          label: "Views and Routes",
          link: {
            type: "doc",
            id: "core/views-and-routes/overview",
          },
          collapsed: true,
          items: [
            // 'documentation/views-and-routes/types-of-views',
            "core/views-and-routes/creating-a-view",
            "core/views-and-routes/assigning-route-to-a-view",
          ],
        },
        {
          type: "category",
          label: "Templates",
          link: {
            type: "doc",
            id: "core/templates/overview",
          },
          collapsed: true,
          items: [],
        },
        {
          type: "category",
          label: "Models",
          link: {
            type: "doc",
            id: "core/ddms/overview",
          },
          collapsed: true,
          items: [
            "core/ddms/creating-a-ddm",
            "core/ddms/ddm-field-types",
            "core/ddms/migrating-ddms",
          ],
        },
      ],
    },
    {
      type: "category",
      label: "Async Tasks",
      link: {
        type: "doc",
        id: "core/async-tasks/overview",
      },
      collapsed: true,
      items: [
        "core/async-tasks/creating-an-async-task",
        "core/async-tasks/syncing-and-viewing-async-tasks",
        "core/async-tasks/manually-triggering-async-tasks",
        "core/async-tasks/scheduling-async-tasks",
      ],
    },
    // {
    //   type: 'category',
    //   label: 'Events',
    //   link: {
    //     type: 'doc',
    //     id: 'documentation/events/overview',
    //   },
    //   collapsed: true,
    //   items: [
    //   ],
    // },
    // {
    //   type: 'category',
    //   label: 'Static and Media',
    //   link: {
    //     type: 'doc',
    //     id: 'documentation/static-and-media/overview',
    //   },
    //   collapsed: true,
    //   items: [
    //   ],
    // },
    // {
    //   type: 'category',
    //   label: 'Deployment',
    //   link: {
    //     type: 'doc',
    //     id: 'documentation/deployment/overview',
    //   },
    //   collapsed: true,
    //   items: [
    //   ],
    // },
  ],
};

module.exports = sidebars;
