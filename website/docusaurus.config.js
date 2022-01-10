/** @type {import('@docusaurus/types').DocusaurusConfig} */
module.exports = {
  title: 'Conductor',
  tagline: 'A simple and elegant research computing orchestrator.',
  url: 'https://www.geoffreyyu.com/conductor/',
  baseUrl: '/conductor/',
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',
  favicon: 'img/ConductorFavicon64.png',
  organizationName: 'geoffxy',
  projectName: 'conductor',
  themeConfig: {
    navbar: {
      title: 'Conductor',
      logo: {
        alt: 'Conductor',
        src: 'img/ConductorLogo_Light.png',
        srcDark: 'img/ConductorLogo_Dark.png',
      },
      items: [
        {
          href: 'https://github.com/geoffxy/conductor/',
          label: 'GitHub',
          position: 'left',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [],
      copyright: `Copyright © ${new Date().getFullYear()} Geoffrey Yu.`,
    },
    prism: {
      theme: require('prism-react-renderer/themes/github'),
      darkTheme: require('prism-react-renderer/themes/palenight'),
      additionalLanguages: ['toml'],
    },
  },
  presets: [
    [
      '@docusaurus/preset-classic',
      {
        docs: {
          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl:
            'https://github.com/geoffxy/conductor/edit/master/website/',
        },
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
        gtag: {
          trackingID: 'G-WVRJT3RWC2',
          anonymizeIP: true,
        },
      },
    ],
  ],
};
