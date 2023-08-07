// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require("prism-react-renderer/themes/github");
const darkCodeTheme = require("prism-react-renderer/themes/dracula");

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "ZOSP",
  tagline: "Next-Gen HealthCare App Development Platform",
  favicon: "img/favicon.ico",

  // Set the production url of your site here
  url: "https://zelthystatichosting.s3.ap-south-1.amazonaws.com",
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: "/zelthy3/docs/",

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: "facebook", // Usually your GitHub org/user name.
  projectName: "docusaurus", // Usually your repo name.

  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",

  // Even if you don't use internalization, you can use this field to set useful
  // metadata like html lang. For example, if your site is Chinese, you may want
  // to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  stylesheets: [
    // String format.
    "https://fonts.googleapis.com",
    "https://fonts.gstatic.com",
    "https://fonts.googleapis.com/css2?family=Lato:wght@400;700;900&family=Source+Code+Pro:wght@400;600;700&display=swap",
  ],

  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve("./sidebars.js"),
          // Remove this to remove the "edit this page" links.
          editUrl:
            "https://github.com/Healthlane-Technologies/zelthy3/tree/documentation/docs",
        },
        blog: {
          showReadingTime: true,
          // Remove this to remove the "edit this page" links.
          editUrl:
            "https://github.com/Healthlane-Technologies/zelthy3/tree/documentation/docs",
        },
        theme: {
          customCss: require.resolve("./src/css/custom.css"),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      image: "img/zelthy-social-card.jpg",
      navbar: {
        title: "ZOSP",
        logo: {
          alt: "Zelthy Logo",
          src: "img/zelthy_logo.png",
        },
        items: [
          {
            type: "docSidebar",
            sidebarId: "docsSidebar",
            position: "left",
            label: "Docs",
          },
          {
            type: "docSidebar",
            sidebarId: "tutorialSidebar",
            position: "left",
            label: "Tutorial",
          },
          { to: "/blog", label: "Blog", position: "left" },
          {
            href: "https://github.com/Healthlane-Technologies/zelthy3",
            position: "right",
            className: "header-github-link",
          },
        ],
      },
      footer: {
        style: "dark",
        links: [
          {
            title: "Docs",
            items: [
              {
                label: "Documentation",
                to: "/docs/documentation/introduction",
              },
              {
                label: "Tutorial",
                to: "/docs/tutorials/todo-app/overview",
              },
            ],
          },
          {
            title: "Others",
            items: [
              {
                label: "Blogs",
                to: "/blog",
              },
            ],
          },
          // {
          //   title: 'Community',
          //   items: [
          //     {
          //       label: 'Stack Overflow',
          //       href: 'https://stackoverflow.com/questions/tagged/docusaurus',
          //     },
          //     {
          //       label: 'Discord',
          //       href: 'https://discordapp.com/invite/docusaurus',
          //     },
          //     {
          //       label: 'Twitter',
          //       href: 'https://twitter.com/docusaurus',
          //     },
          //   ],
          // },
          {
            title: "More",
            items: [
              {
                label: "Zelthy",
                href: "https://zelthy.com",
              },
              {
                label: "GitHub",
                href: "https://github.com/Healthlane-Technologies/zelthy3",
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Healthlane Technologies Pvt. Ltd.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
      },
    }),

  plugins: [require.resolve("@cmfcmf/docusaurus-search-local")],
};

module.exports = config;
