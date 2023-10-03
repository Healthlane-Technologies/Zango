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
  tutorialSidebar: [
    {
      type: 'category',
      label: 'Simple Todo App',
      link: {
        type: 'doc',
        id: 'tutorials/todo-app/overview',
      },
      collapsed: false,
      items: [
      ],
    },
    {
      type: 'category',
      label: 'Complex App',
      link: {
        type: 'doc',
        id: 'tutorials/complex-app/overview',
      },
      collapsed: false,
      items: [
      ],
    },
  ],
  docsSidebar: [
    'documentation/introduction',
    {
      type: 'category',
      label: 'Getting Started',
      link: {
        type: 'generated-index',
      },
      collapsed: true,
      items: [
        'documentation/getting-started/installing-zosp',
        'documentation/getting-started/zelthy3-the-zelthy-cli',
        'documentation/getting-started/prerequisites-for-a-project',
        'documentation/getting-started/setting-up-the-project',
        'documentation/getting-started/running-development-server',
        'documentation/getting-started/accessing-z-dynamic',
      ],
    },
    {
      type: 'category',
      label: 'Spinning up an app',
      link: {
        type: 'generated-index',
      },
      collapsed: true,
      items: [
        'documentation/spinning-up-an-app/creating-an-app',
        'documentation/spinning-up-an-app/intializing-app-codebase',
        'documentation/spinning-up-an-app/switching-to-app-view',
        'documentation/spinning-up-an-app/updating-app-settings',
        'documentation/spinning-up-an-app/updating-app-theme',
      ],
    },
    {
      type: 'category',
      label: 'User Roles',
      link: {
        type: 'doc',
        id: 'documentation/user-roles/overview',
      },
      collapsed: true,
      items: [
        'documentation/user-roles/creating-a-user-role',
        'documentation/user-roles/assigning-policies-to-user-roles',
        'documentation/user-roles/deactivating-a-user-role',
        'documentation/user-roles/reserved-user-roles',
      ],
    },
    {
      type: 'category',
      label: 'User Management',
      link: {
        type: 'doc',
        id: 'documentation/user-management/overview',
      },
      collapsed: true,
      items: [
        'documentation/user-management/viewing-users',
        'documentation/user-management/adding-users',
        'documentation/user-management/assigning-policies-to-users',
        'documentation/user-management/updating-user-roles',
      ],
    },
    {
      type: 'category',
      label: 'Modules',
      link: {
        type: 'doc',
        id: 'documentation/modules/overview',
      },
      collapsed: true,
      items: [
        'documentation/modules/creating-a-module',
        'documentation/modules/registering-a-module',
      ],
    },
    {
      type: 'category',
      label: 'Views and Routes',
      link: {
        type: 'doc',
        id: 'documentation/views-and-routes/overview',
      },
      collapsed: true,
      items: [
        'documentation/views-and-routes/types-of-views',
        'documentation/views-and-routes/creating-a-view',
        'documentation/views-and-routes/assigning-route-to-a-view',
      ],
    },
    {
      type: 'category',
      label: 'Templates',
      link: {
        type: 'doc',
        id: 'documentation/templates/overview',
      },
      collapsed: true,
      items: [
      ],
    },
    {
      type: 'category',
      label: 'Dynamic Data Models',
      link: {
        type: 'doc',
        id: 'documentation/ddms/overview',
      },
      collapsed: true,
      items: [
        'documentation/ddms/creating-a-ddm',
        'documentation/ddms/ddm-field-types',
        'documentation/ddms/migrating-ddms',
      ],
    },
    {
      type: 'category',
      label: 'Permission Framework',
      link: {
        type: 'doc',
        id: 'documentation/permission-framework/overview',
      },
      collapsed: true,
      items: [
        {
          type: 'category',
          label: 'Permissions',
          link: {
            type: 'doc',
            id: 'documentation/permission-framework/permissions/overview',
          },
          collapsed: true,
          items: [
            'documentation/permission-framework/permissions/creating-permissions',
            'documentation/permission-framework/permissions/syncing-and-viewing-permissions',
            'documentation/permission-framework/permissions/using-permissions',
            'documentation/permission-framework/permissions/custom-permissions',
          ],
        },
        {
          type: 'category',
          label: 'Policies',
          link: {
            type: 'doc',
            id: 'documentation/permission-framework/policies/overview',
          },
          collapsed: true,
          items: [
            'documentation/permission-framework/policies/viewing-policies',
            'documentation/permission-framework/policies/creating-a-policy',
            'documentation/permission-framework/policies/policy-config-json',
            'documentation/permission-framework/policies/assigning-policies',
            'documentation/permission-framework/policies/editing-policy-config',
            'documentation/permission-framework/policies/archiving-a-policy',
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'Packages',
      link: {
        type: 'doc',
        id: 'documentation/packages/overview',
      },
      collapsed: true,
      items: [
        'documentation/packages/installing-a-package',
      ],
    },
    {
      type: 'category',
      label: 'Async Tasks',
      link: {
        type: 'doc',
        id: 'documentation/async-tasks/overview',
      },
      collapsed: true,
      items: [
        'documentation/async-tasks/creating-an-async-task',
      ],
    },
    {
      type: 'category',
      label: 'Events',
      link: {
        type: 'doc',
        id: 'documentation/events/overview',
      },
      collapsed: true,
      items: [
      ],
    },
    {
      type: 'category',
      label: 'Static and Media',
      link: {
        type: 'doc',
        id: 'documentation/static-and-media/overview',
      },
      collapsed: true,
      items: [
      ],
    },
    {
      type: 'category',
      label: 'Deployment',
      link: {
        type: 'doc',
        id: 'documentation/deployment/overview',
      },
      collapsed: true,
      items: [
      ],
    },
  ],
};

module.exports = sidebars;
