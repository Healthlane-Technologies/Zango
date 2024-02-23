// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require("prism-react-renderer/themes/github");
const darkCodeTheme = require("prism-react-renderer/themes/dracula");

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "Zelthy Docs",
  tagline: "Next-Gen HealthCare App Development Platform",
  favicon: "img/favicon.ico",

  // Set the production url of your site here
  url: "https://zelthystatichosting.s3.ap-south-1.amazonaws.com",
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: "/",

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: "zelthy", // Usually your GitHub org/user name.
  projectName: "zelthy_docs", // Usually your repo name.

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
        title: "Zelthy Docs",
        logo: {
          alt: "Zelthy Logo",
          src: "img/zelthy_logo.png",
          href: '/docs/documentation/introduction'
        },
        items: [
          {
            type: "docSidebar",
            sidebarId: "docsSidebar",
            position: "left",
            label: "Docs",
          },
          {
            label: "Packages", 
            position: "left",
            type: "dropdown",
            items: [
                {
                  label: "Login",
                  to: "/login"
                },
                {
                  label: "Frame",
                  to: "/frame"
                },
                {
                  label: "Crud",
                  to: "/crud"
                }
              ]
          },
          // {
          //   href: "https://github.com/Healthlane-Technologies/zelthy3",
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
        selector: '.markdown img',
        background: {
          light: 'rgb(255, 255, 255)',
          dark: 'rgb(50, 50, 50)'
        },
        config: {
          // options you can specify via https://github.com/francoischalifour/medium-zoom#usage
          margin: 36
        }
      }
    }),

  plugins: [
    require.resolve("@cmfcmf/docusaurus-search-local"),
    'docusaurus-plugin-image-zoom'
  ],
};

module.exports = config;
