// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion
const zdocConfig = require("./zdocs.config.json");

const lightCodeTheme = require("prism-react-renderer/themes/github");
const darkCodeTheme = require("prism-react-renderer/themes/dracula");

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "Zango Docs",
  tagline: "Next-Gen Business App Development Platform",
  favicon: "img/favicon.ico",

  // Set the production url of your site here
  url: "https://www.zango.dev/",
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: "/",

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: "zelthy", // Usually your GitHub org/user name.
  projectName: "zango_docs", // Usually your repo name.

  onBrokenLinks: "ignore",
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
            "https://github.com/Healthlane-Technologies/zango/tree/documentation/docs",
          path: "./docs", // path to your docs folder
          routeBasePath: "/", //path/word that you want to set
        },
        blog: {
          showReadingTime: true,
          // Remove this to remove the "edit this page" links.
          editUrl:
            "https://github.com/Healthlane-Technologies/zango/tree/documentation/docs",
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
        // title: "Zelthy Docs",
        logo: {
          alt: "Zango Logo",
          src: "img/zango_logo_blk_1.png",
          srcDark: "img/zango_logo.svg",
          href: "/core/introduction",
          style: { width: '100px', height: 'auto',  display: 'flex', alignItems: 'center', paddingTop: '5px' } // Adjust width as needed
        },
        items: [
          {
            type: "docSidebar",
            sidebarId: "docsSidebar",
            position: "left",
            label: "Docs",
          },
          ...zdocConfig?.navbar?.items,
          // {
          //   href: "https://github.com/Healthlane-Technologies/zango/",
          //   position: "right",
          //   className: "header-github-link",
          // },
        ],
      },
      footer: {
        style: "dark",
        links: [
          // {
          //   title: "Docs",
          //   items: [
          //     {
          //       label: "Documentation",
          //       to: "/docs/documentation/introduction",
          //     },
          //     // {
          //     //   label: "Tutorial",
          //     //   to: "/docs/tutorials/todo-app/overview",
          //     // },
          //   ],
          // },
          // {
          //   title: "Others",
          //   items: [
          //   ],
          // },
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
          // {
          //   title: "More",
          //   items: [
          //     {
          //       label: "Zelthy",
          //       href: "https://zelthy.com",
          //     },
          //     {
          //       label: "GitHub",
          //       href: "https://github.com/Healthlane-Technologies/zelthy3",
          //     },
          //   ],
          // },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Healthlane Technologies Pvt. Ltd.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
      },
      zoom: {
        selector: ".markdown img",
        background: {
          light: "rgb(255, 255, 255)",
          dark: "rgb(50, 50, 50)",
        },
        config: {
          // options you can specify via https://github.com/francoischalifour/medium-zoom#usage
          margin: 36,
        },
      },
      algolia: {
        // The application ID provided by Algolia
        appId: "YZ5AZ15C2L",

        // Public API key: it is safe to commit it
        apiKey: "669aeed650b1db0aae9d3d2c4508157e",

        indexName: "zcore",

        // Optional: see doc section below
        contextualSearch: true,

        // Optional: Specify domains where the navigation should occur through window.location instead on history.push. Useful when our Algolia config crawls multiple documentation sites and we want to navigate with window.location.href to them.
        // externalUrlRegex: "external\\.com|domain\\.com",

        // Optional: Replace parts of the item URLs from Algolia. Useful when using the same search index for multiple deployments using a different baseUrl. You can use regexp or string in the `from` param. For example: localhost:3000 vs myCompany.com/docs
        // replaceSearchResultPathname: {
        //   from: "/", // or as RegExp: /\/docs\//
        //   to: "/",
        // },

        // Optional: Algolia search parameters
        searchParameters: {},

        // Optional: path for search page that enabled by default (`false` to disable it)
        searchPagePath: "search",

        //... other Algolia params
      },
    }),

  plugins: [
    // require.resolve("@cmfcmf/docusaurus-search-local"),
    "docusaurus-plugin-image-zoom",
    // [
    //   "vercel-analytics",
    //   {
    //     debug: true,
    //     mode: "auto",
    //   },
    // ],
    ...zdocConfig.plugins,
  ],
};

module.exports = config;
