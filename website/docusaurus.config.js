/** @type {import('@docusaurus/types').DocusaurusConfig} */
module.exports = {
  title: 'Conductor',
  tagline: 'A simple and elegant research computing orchestrator.',
  url: 'https://www.geoffreyyu.com/conductor/',
  baseUrl: '/',
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',
  favicon: 'img/favicon.ico',
  organizationName: 'geoffxy',
  projectName: 'conductor',
  themeConfig: {
    navbar: {
      title: 'Conductor',
      logo: {
        alt: 'My Site Logo',
        src: 'img/logo.svg',
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
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      },
    ],
  ],
};