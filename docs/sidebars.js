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
        'documentation/getting-started/creating-a-project'
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
        'documentation/spinning-up-an-app/updating-the-app-settings',
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
        'documentation/templates/creating-a-template',
      ],
    },
    {
      type: 'category',
      label: 'APIs and Views',
      link: {
        type: 'doc',
        id: 'documentation/apis-and-views/overview',
      },
      collapsed: true,
      items: [
        'documentation/apis-and-views/creating-an-api',
        'documentation/apis-and-views/creating-a-view',
      ],
    },
    {
      type: 'category',
      label: 'Permissions',
      link: {
        type: 'doc',
        id: 'documentation/permissions/overview',
      },
      collapsed: true,
      items: [
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
